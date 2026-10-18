#include "decoder.h"

#include <cstring>
#include <stdexcept>
#include <unordered_map>

#include "ocgapi_constants.h"

namespace ygo_gym::event {
namespace {

class Reader {
public:
    Reader(const std::uint8_t* data, std::size_t size) : data_(data), size_(size) {}

    template<typename T>
    T read() {
        if(position_ + sizeof(T) > size_)
            throw std::runtime_error("truncated ocgcore event message");
        T value{};
        std::memcpy(&value, data_ + position_, sizeof(T));
        position_ += sizeof(T);
        return value;
    }

    [[nodiscard]] std::size_t remaining() const noexcept { return size_ - position_; }

private:
    const std::uint8_t* data_;
    std::size_t size_;
    std::size_t position_{0};
};

Locator read_location(Reader& reader) {
    return Locator{
        reader.read<std::uint8_t>(),
        reader.read<std::uint8_t>(),
        reader.read<std::uint32_t>(),
        reader.read<std::uint32_t>(),
    };
}

struct LocatorKey {
    std::uint8_t controller{};
    std::uint32_t location{};
    std::uint32_t sequence{};
    bool operator==(const LocatorKey& other) const noexcept {
        return controller == other.controller && location == other.location && sequence == other.sequence;
    }
};

struct LocatorHash {
    std::size_t operator()(const LocatorKey& value) const noexcept {
        std::size_t hash = value.controller;
        hash = hash * 1315423911u + value.location;
        hash = hash * 1315423911u + value.sequence;
        return hash;
    }
};

LocatorKey key(const Locator& value) {
    return LocatorKey{value.controller, value.location, value.sequence};
}

class Builder {
public:
    void message(const std::uint8_t* data, std::size_t size) {
        if(size == 0)
            return;
        Reader reader(data, size);
        const auto type = reader.read<std::uint8_t>();
        switch(type) {
        case MSG_WIN:
            win(reader);
            break;
        case MSG_CONFIRM_DECKTOP:
        case MSG_CONFIRM_EXTRATOP:
        case MSG_CONFIRM_CARDS:
            confirm(reader, type);
            break;
        case MSG_SHUFFLE_DECK:
            shuffle_simple(reader, LOCATION_DECK);
            break;
        case MSG_SHUFFLE_HAND:
            shuffle_cards(reader, LOCATION_HAND);
            break;
        case MSG_SHUFFLE_EXTRA:
            shuffle_cards(reader, LOCATION_EXTRA);
            break;
        case MSG_SWAP_GRAVE_DECK: {
            const auto player = reader.read<std::uint8_t>();
            transition_.events.emplace_back(GraveDeckSwapEvent{player});
            clear_zone(player, LOCATION_DECK);
            clear_zone(player, LOCATION_GRAVE);
            break;
        }
        case MSG_REVERSE_DECK:
            transition_.events.emplace_back(DeckReverseEvent{});
            clear_zone(0xff, LOCATION_DECK);
            break;
        case MSG_DECK_TOP:
            deck_top(reader);
            break;
        case MSG_NEW_TURN:
            transition_.events.emplace_back(TurnEvent{reader.read<std::uint8_t>()});
            break;
        case MSG_NEW_PHASE:
            transition_.events.emplace_back(PhaseEvent{reader.read<std::uint16_t>()});
            break;
        case MSG_MOVE:
            move(reader);
            break;
        case MSG_POS_CHANGE:
            position(reader);
            break;
        case MSG_SET:
            set(reader);
            break;
        case MSG_SUMMONING:
            summon(reader, SummonKind::normal, SummonStage::attempt, true);
            break;
        case MSG_SUMMONED:
            complete_summon(SummonKind::normal);
            break;
        case MSG_SPSUMMONING:
            summon(reader, SummonKind::special, SummonStage::attempt, false);
            break;
        case MSG_SPSUMMONED:
            complete_summon(SummonKind::special);
            break;
        case MSG_FLIPSUMMONING:
            summon(reader, SummonKind::flip, SummonStage::attempt, true);
            break;
        case MSG_FLIPSUMMONED:
            complete_summon(SummonKind::flip);
            break;
        case MSG_CHAINING:
            chaining(reader);
            break;
        case MSG_CHAINED:
            chain_stage(reader, ChainStage::added);
            break;
        case MSG_CHAIN_SOLVING:
            chain_stage(reader, ChainStage::resolving);
            break;
        case MSG_CHAIN_SOLVED:
            chain_stage(reader, ChainStage::resolved);
            break;
        case MSG_CHAIN_NEGATED:
            chain_stage(reader, ChainStage::negated);
            break;
        case MSG_CHAIN_DISABLED:
            chain_stage(reader, ChainStage::disabled);
            break;
        case MSG_CHAIN_END:
            transition_.events.emplace_back(ChainEvent{ChainStage::ended, std::nullopt, std::nullopt, std::nullopt, std::nullopt});
            chain_.clear();
            break;
        case MSG_DRAW:
            draw(reader);
            break;
        case MSG_DAMAGE:
            life(reader, LifePointKind::damage);
            break;
        case MSG_RECOVER:
            life(reader, LifePointKind::recover);
            break;
        case MSG_PAY_LPCOST:
            life(reader, LifePointKind::pay);
            break;
        case MSG_LPUPDATE:
            life_set(reader);
            break;
        case MSG_ADD_COUNTER:
            counter(reader, 1);
            break;
        case MSG_REMOVE_COUNTER:
            counter(reader, -1);
            break;
        case MSG_EQUIP:
            relation(reader, RelationEventKind::equip);
            break;
        case MSG_CARD_TARGET:
            relation(reader, RelationEventKind::target);
            break;
        case MSG_CANCEL_TARGET:
            relation(reader, RelationEventKind::cancel_target);
            break;
        case MSG_ATTACK:
            attack(reader);
            break;
        case MSG_BATTLE:
            battle(reader);
            break;
        case MSG_TOSS_COIN:
            random(reader, RandomKind::coin);
            break;
        case MSG_TOSS_DICE:
            random(reader, RandomKind::dice);
            break;
        case MSG_DAMAGE_STEP_START:
            transition_.events.emplace_back(DamageStepEvent{DamageStepStage::start});
            break;
        case MSG_DAMAGE_STEP_END:
            transition_.events.emplace_back(DamageStepEvent{DamageStepStage::end});
            break;
        default:
            break;
        }
    }

    Transition finish() { return std::move(transition_); }

private:
    std::uint32_t card(std::uint32_t code, std::uint8_t visible_to, std::optional<Locator> current) {
        if(current && current->location != 0) {
            const auto found = located_.find(key(*current));
            if(found != located_.end()) {
                auto& existing = transition_.cards[found->second];
                existing.visible_to |= visible_to;
                existing.current = current;
                if(existing.code == 0)
                    existing.code = code;
                return found->second;
            }
        }
        const auto id = static_cast<std::uint32_t>(transition_.cards.size());
        transition_.cards.push_back(RawCard{code, visible_to, current});
        if(current && current->location != 0)
            located_[key(*current)] = id;
        return id;
    }

    std::uint32_t moved_card(std::uint32_t code, std::uint8_t visible_to, const Locator& previous, const Locator& current) {
        std::optional<std::uint32_t> found_id;
        if(previous.location != 0) {
            const auto found = located_.find(key(previous));
            if(found != located_.end()) {
                found_id = found->second;
                located_.erase(found);
            }
        }
        if(!found_id)
            return card(code, visible_to, current.location == 0 ? std::nullopt : std::optional<Locator>{current});
        auto& existing = transition_.cards[*found_id];
        existing.code = code;
        existing.visible_to |= visible_to;
        existing.current = current.location == 0 ? std::nullopt : std::optional<Locator>{current};
        if(current.location != 0)
            located_[key(current)] = *found_id;
        return *found_id;
    }

    void clear_zone(std::uint8_t player, std::uint32_t location) {
        for(auto it = located_.begin(); it != located_.end();) {
            if((player == 0xff || it->first.controller == player) && it->first.location == location)
                it = located_.erase(it);
            else
                ++it;
        }
    }

    void win(Reader& reader) {
        const auto winner = reader.read<std::uint8_t>();
        const auto reason = reader.read<std::uint8_t>();
        transition_.events.emplace_back(WinEvent{winner <= 1 ? std::optional<std::uint8_t>{winner} : std::nullopt, reason});
    }

    void confirm(Reader& reader, std::uint8_t type) {
        const auto player = reader.read<std::uint8_t>();
        const auto count = reader.read<std::uint32_t>();
        for(std::uint32_t i = 0; i < count; ++i) {
            const auto code = reader.read<std::uint32_t>();
            Locator location{};
            location.controller = reader.read<std::uint8_t>();
            location.location = reader.read<std::uint8_t>();
            location.sequence = reader.read<std::uint32_t>();
            std::uint8_t visible = 0x3;
            if(type == MSG_CONFIRM_CARDS && (location.location == LOCATION_DECK || location.location == LOCATION_EXTRA))
                visible = static_cast<std::uint8_t>(1u << player);
            const auto id = card(code, visible, location);
            transition_.events.emplace_back(RevealEvent{id});
        }
    }

    void shuffle_simple(Reader& reader, std::uint32_t location) {
        const auto player = reader.read<std::uint8_t>();
        transition_.events.emplace_back(ShuffleEvent{player, location});
        clear_zone(player, location);
    }

    void shuffle_cards(Reader& reader, std::uint32_t location) {
        const auto player = reader.read<std::uint8_t>();
        const auto count = reader.read<std::uint32_t>();
        for(std::uint32_t i = 0; i < count; ++i)
            (void)reader.read<std::uint32_t>();
        transition_.events.emplace_back(ShuffleEvent{player, location});
        clear_zone(player, location);
    }

    void deck_top(Reader& reader) {
        const auto player = reader.read<std::uint8_t>();
        const auto offset = reader.read<std::uint32_t>();
        const auto code = reader.read<std::uint32_t>();
        const auto position = reader.read<std::uint32_t>();
        (void)offset;
        (void)player;
        (void)position;
        const auto id = card(code, 0x3, std::nullopt);
        transition_.events.emplace_back(RevealEvent{id});
    }

    void move(Reader& reader) {
        const auto code = reader.read<std::uint32_t>();
        const auto previous = read_location(reader);
        const auto current = read_location(reader);
        const auto reason = reader.read<std::uint32_t>();
        std::uint8_t visible = static_cast<std::uint8_t>(1u << current.controller);
        const bool public_destination = (current.location & (LOCATION_GRAVE | LOCATION_OVERLAY)) != 0
            || (((current.location & (LOCATION_DECK | LOCATION_HAND)) == 0) && ((current.position & POS_FACEDOWN) == 0));
        if(public_destination || current.location == 0)
            visible = 0x3;
        const auto id = moved_card(code, visible, previous, current);
        transition_.events.emplace_back(MoveEvent{id, previous, current, reason});
    }

    void position(Reader& reader) {
        const auto code = reader.read<std::uint32_t>();
        const auto controller = reader.read<std::uint8_t>();
        const auto location = reader.read<std::uint8_t>();
        const auto sequence = reader.read<std::uint8_t>();
        const auto previous = reader.read<std::uint8_t>();
        const auto current = reader.read<std::uint8_t>();
        Locator locator{controller, location, sequence, current};
        const auto id = card(code, 0x3, locator);
        transition_.events.emplace_back(PositionEvent{id, controller, location, sequence, previous, current});
    }

    void set(Reader& reader) {
        const auto code = reader.read<std::uint32_t>();
        const auto location = read_location(reader);
        const auto visible = static_cast<std::uint8_t>(1u << location.controller);
        const auto id = card(code, visible, location);
        transition_.events.emplace_back(SetEvent{id});
    }

    void summon(Reader& reader, SummonKind kind, SummonStage stage, bool public_code) {
        const auto code = reader.read<std::uint32_t>();
        const auto location = read_location(reader);
        std::uint8_t visible = 0x3;
        if(!public_code && (location.position & POS_FACEDOWN) != 0)
            visible = static_cast<std::uint8_t>(1u << location.controller);
        const auto id = card(code, visible, location);
        latest_summon_[static_cast<std::size_t>(kind)] = std::make_pair(id, location.controller);
        transition_.events.emplace_back(SummonEvent{id, location.controller, kind, stage});
    }

    void complete_summon(SummonKind kind) {
        const auto& latest = latest_summon_[static_cast<std::size_t>(kind)];
        if(latest)
            transition_.events.emplace_back(SummonEvent{latest->first, latest->second, kind, SummonStage::complete});
    }

    void chaining(Reader& reader) {
        const auto code = reader.read<std::uint32_t>();
        const auto handler = read_location(reader);
        const auto player = reader.read<std::uint8_t>();
        (void)reader.read<std::uint8_t>();
        (void)reader.read<std::uint32_t>();
        const auto description = reader.read<std::uint64_t>();
        const auto index = reader.read<std::uint32_t>();
        const auto id = card(code, 0x3, handler);
        chain_[index] = ChainMeta{id, player, description};
        transition_.events.emplace_back(ChainEvent{ChainStage::activating, id, player, description, index});
    }

    void chain_stage(Reader& reader, ChainStage stage) {
        const auto index = static_cast<std::uint32_t>(reader.read<std::uint8_t>());
        const auto found = chain_.find(index);
        if(found == chain_.end()) {
            transition_.events.emplace_back(ChainEvent{stage, std::nullopt, std::nullopt, std::nullopt, index});
            return;
        }
        transition_.events.emplace_back(ChainEvent{stage, found->second.card, found->second.player, found->second.description, index});
    }

    void draw(Reader& reader) {
        const auto player = reader.read<std::uint8_t>();
        const auto count = reader.read<std::uint32_t>();
        for(std::uint32_t i = 0; i < count; ++i) {
            const auto code = reader.read<std::uint32_t>();
            const auto position = reader.read<std::uint32_t>();
            auto visible = static_cast<std::uint8_t>(1u << player);
            if((position & POS_FACEUP) != 0)
                visible = 0x3;
            const auto id = card(code, visible, std::nullopt);
            transition_.events.emplace_back(DrawEvent{player, id});
        }
    }

    void life(Reader& reader, LifePointKind kind) {
        const auto player = reader.read<std::uint8_t>();
        const auto amount = reader.read<std::uint32_t>();
        transition_.events.emplace_back(LifePointEvent{player, amount, kind});
    }

    void life_set(Reader& reader) {
        const auto player = reader.read<std::uint8_t>();
        const auto value = reader.read<std::uint32_t>();
        transition_.events.emplace_back(LifePointEvent{player, value, LifePointKind::set});
    }

    void counter(Reader& reader, int sign) {
        const auto type = reader.read<std::uint16_t>();
        Locator location{};
        location.controller = reader.read<std::uint8_t>();
        location.location = reader.read<std::uint8_t>();
        location.sequence = reader.read<std::uint8_t>();
        const auto count = reader.read<std::uint16_t>();
        const auto id = card(0, 0x3, location);
        transition_.events.emplace_back(CounterEvent{id, type, static_cast<std::int32_t>(count) * sign});
    }

    void relation(Reader& reader, RelationEventKind kind_value) {
        const auto source_location = read_location(reader);
        const auto target_location = read_location(reader);
        const auto source = card(0, 0x3, source_location);
        const auto target = card(0, 0x3, target_location);
        transition_.events.emplace_back(RelationEvent{kind_value, source, target});
    }

    void attack(Reader& reader) {
        const auto attacker_location = read_location(reader);
        const auto target_location = read_location(reader);
        const auto attacker = card(0, 0x3, attacker_location);
        std::optional<std::uint32_t> target;
        if(target_location.location != 0)
            target = card(0, 0x3, target_location);
        transition_.events.emplace_back(AttackEvent{attacker, target});
    }

    void battle(Reader& reader) {
        const auto attacker_location = read_location(reader);
        const auto attacker = card(0, 0x3, attacker_location);
        const auto attacker_attack = reader.read<std::uint32_t>();
        const auto attacker_defense = reader.read<std::uint32_t>();
        const auto attacker_destroyed = reader.read<std::uint8_t>() != 0;
        const auto target_location = read_location(reader);
        const auto target_attack = reader.read<std::uint32_t>();
        const auto target_defense = reader.read<std::uint32_t>();
        const auto target_destroyed = reader.read<std::uint8_t>() != 0;
        std::optional<std::uint32_t> target;
        if(target_location.location != 0)
            target = card(0, 0x3, target_location);
        transition_.events.emplace_back(BattleEvent{
            attacker,
            static_cast<std::int32_t>(attacker_attack),
            static_cast<std::int32_t>(attacker_defense),
            attacker_destroyed,
            target,
            static_cast<std::int32_t>(target_attack),
            static_cast<std::int32_t>(target_defense),
            target_destroyed,
        });
    }

    void random(Reader& reader, RandomKind kind_value) {
        const auto player = reader.read<std::uint8_t>();
        const auto count = reader.read<std::uint8_t>();
        std::vector<std::uint8_t> results;
        results.reserve(count);
        for(std::uint8_t i = 0; i < count; ++i)
            results.push_back(reader.read<std::uint8_t>());
        transition_.events.emplace_back(RandomEvent{player, kind_value, std::move(results)});
    }

    struct ChainMeta { std::uint32_t card{}; std::uint8_t player{}; std::uint64_t description{}; };
    Transition transition_;
    std::unordered_map<LocatorKey, std::uint32_t, LocatorHash> located_;
    std::unordered_map<std::uint32_t, ChainMeta> chain_;
    std::optional<std::pair<std::uint32_t, std::uint8_t>> latest_summon_[3];
};

}

Transition decode(const std::vector<std::uint8_t>& messages) {
    Builder builder;
    std::size_t offset = 0;
    while(offset < messages.size()) {
        if(messages.size() - offset < sizeof(std::uint32_t))
            throw std::runtime_error("truncated ocgcore message frame");
        std::uint32_t size = 0;
        std::memcpy(&size, messages.data() + offset, sizeof(size));
        offset += sizeof(size);
        if(size > messages.size() - offset)
            throw std::runtime_error("ocgcore message frame length exceeds the available data");
        builder.message(messages.data() + offset, size);
        offset += size;
    }
    return builder.finish();
}

}
