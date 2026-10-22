#include "duel/duel.h"
#include "event/decoding/decoder.h"
#include "ygopro-core/clone/persistence/api.h"
#include "ygopro-core/clone/persistence/stream.h"
#include <stdexcept>
namespace ygo_gym {
namespace {
void blob(ocg::persistence::Stream &stream, std::vector<std::uint8_t> &bytes) {
    auto size = stream.count(bytes.size());
    if (stream.reading)
        bytes.resize(size);
    stream.bytes(bytes.data(), size);
}
} // namespace
std::vector<std::uint8_t> Duel::serialize() const {
    if (closed() || terminated_ || status_ != OCG_DUEL_STATUS_AWAITING || !decision_ ||
        !action_state_ || !observation_)
        throw std::runtime_error("snapshot capture requires an open awaiting duel");
    if (!script_errors_.empty())
        throw std::runtime_error("cannot save a duel with pending script errors");
    auto core = ocg::persistence::save(*static_cast<duel *>(duel_));
    std::vector<std::uint8_t> data;
    ocg::persistence::Stream stream(data, false);
    blob(stream, core);
    auto messages = message_buffer_;
    blob(stream, messages);
    auto selections = action_state_->selection_indices();
    stream.count(selections.size());
    for (auto index : selections)
        stream.scalar(index);
    return data;
}
std::unique_ptr<Duel> Duel::deserialize(std::shared_ptr<const EngineState> engine,
                                        std::vector<std::uint8_t> bytes) {
    ocg::persistence::Stream stream(bytes, true);
    std::vector<std::uint8_t> core, messages;
    blob(stream, core);
    blob(stream, messages);
    std::vector<std::uint32_t> selections(stream.count());
    for (auto &index : selections)
        stream.scalar(index);
    stream.finish();
    auto result = std::unique_ptr<Duel>(new Duel(std::move(engine)));
    const OCG_CloneCallbacks callbacks{&Duel::read_card,
                                       result.get(),
                                       &Duel::read_script,
                                       result.get(),
                                       &Duel::handle_log,
                                       result.get(),
                                       nullptr,
                                       nullptr};
    auto native = ocg::persistence::load(std::move(core), callbacks);
    result->duel_ = native.release();
    result->status_ = OCG_DUEL_STATUS_AWAITING;
    result->message_buffer_ = std::move(messages);
    result->transition_events_ = event::decode(result->message_buffer_);
    result->update_decision();
    for (auto index : selections) {
        if (result->action_state_->step(index))
            throw std::invalid_argument("snapshot selection unexpectedly advances the engine");
    }
    if (!selections.empty()) {
        result->transition_events_ = {};
        auto storage =
            std::make_shared<state::ObservationStorage>(*result->observation_->storage());
        storage->pending_actions = result->action_state_->pending_actions();
        storage->events = event::Batch{};
        result->observation_.emplace(state::Observation{std::move(storage)});
    }
    return result;
}
} // namespace ygo_gym
