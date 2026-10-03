#include "legality.h"

#include <algorithm>
#include <array>
#include <cstdint>
#include <limits>
#include <unordered_set>
#include <utility>
#include <vector>

namespace ygo_gym::action {
namespace {

bool contains(const std::vector<std::uint32_t>& values, std::uint32_t value) {
    return std::find(values.begin(), values.end(), value) != values.end();
}

std::array<std::uint32_t, 2> values(std::uint32_t packed) {
    return {packed & 0xffffu, packed >> 16};
}

class SumBits {
public:
    explicit SumBits(std::uint32_t target)
        : target_(target), words_(static_cast<std::size_t>(target) / 64 + 1, 0) {}

    void set(std::uint32_t sum) {
        if(sum <= target_)
            words_[sum / 64] |= std::uint64_t{1} << (sum % 64);
    }

    [[nodiscard]] bool test(std::uint32_t sum) const {
        return sum <= target_ && (words_[sum / 64] & (std::uint64_t{1} << (sum % 64))) != 0;
    }

    [[nodiscard]] bool empty() const {
        return std::all_of(words_.begin(), words_.end(), [](std::uint64_t word) { return word == 0; });
    }

    void add_shifted(const SumBits& source, std::uint32_t shift) {
        if(shift > target_)
            return;

        const auto word_shift = static_cast<std::size_t>(shift / 64);
        const auto bit_shift = static_cast<unsigned>(shift % 64);
        for(std::size_t source_index = 0; source_index < source.words_.size(); ++source_index) {
            const auto word = source.words_[source_index];
            if(word == 0)
                continue;

            const auto destination_index = source_index + word_shift;
            if(destination_index >= words_.size())
                break;

            words_[destination_index] |= word << bit_shift;
            if(bit_shift != 0 && destination_index + 1 < words_.size())
                words_[destination_index + 1] |= word >> (64 - bit_shift);
        }
    }

private:
    std::uint32_t target_;
    std::vector<std::uint64_t> words_;
};

SumBits mandatory_sums(
    const protocol::SumDecision& decision,
    const std::vector<std::uint32_t>& selected
) {
    SumBits sums(decision.target);
    sums.set(0);

    const auto extend = [&](const protocol::SumRef& card) {
        const auto card_values = values(card.value);
        SumBits next(decision.target);
        next.add_shifted(sums, card_values[0]);
        if(card_values[1] != 0 && card_values[1] != card_values[0])
            next.add_shifted(sums, card_values[1]);
        sums = std::move(next);
    };

    for(const auto& card : decision.required)
        extend(card);
    for(const auto index : selected)
        extend(decision.cards[index]);
    return sums;
}

bool exact_can_complete(
    const protocol::SumDecision& decision,
    const std::vector<std::uint32_t>& selected
) {
    if(selected.size() > decision.max)
        return false;

    auto initial = mandatory_sums(decision, selected);
    if(initial.empty())
        return false;

    const auto selected_count = static_cast<std::uint32_t>(selected.size());
    const auto min_additional = selected_count >= decision.min ? 0u : decision.min - selected_count;
    const auto max_additional = decision.max - selected_count;

    std::vector<SumBits> reachable;
    reachable.reserve(max_additional + 1);
    for(std::uint32_t count = 0; count <= max_additional; ++count)
        reachable.emplace_back(decision.target);
    reachable[0] = std::move(initial);

    std::uint32_t considered = 0;
    for(std::uint32_t index = 0; index < decision.cards.size(); ++index) {
        if(contains(selected, index))
            continue;

        ++considered;
        const auto upper = std::min(max_additional, considered);
        const auto card_values = values(decision.cards[index].value);
        for(std::uint32_t count = upper; count > 0; --count) {
            reachable[count].add_shifted(reachable[count - 1], card_values[0]);
            if(card_values[1] != 0 && card_values[1] != card_values[0])
                reachable[count].add_shifted(reachable[count - 1], card_values[1]);
        }
    }

    for(std::uint32_t count = min_additional; count <= max_additional; ++count) {
        if(reachable[count].test(decision.target))
            return true;
    }
    return false;
}

struct Range {
    std::uint32_t minimum{0};
    std::uint32_t maximum{0};
    std::uint32_t smallest{std::numeric_limits<std::uint32_t>::max()};
    bool empty{true};
};

void add(Range& range, const protocol::SumRef& card) {
    const auto card_values = values(card.value);
    const auto minimum = card_values[1] != 0 && card_values[1] < card_values[0] ? card_values[1] : card_values[0];
    range.minimum += minimum;
    range.maximum += std::max(card_values[0], card_values[1]);
    range.smallest = std::min(range.smallest, minimum);
    range.empty = false;
}

Range selected_range(
    const protocol::SumDecision& decision,
    const std::vector<std::uint32_t>& selected
) {
    Range range;
    for(const auto& card : decision.required)
        add(range, card);
    for(const auto index : selected)
        add(range, decision.cards[index]);
    return range;
}

bool range_complete(const Range& range, std::uint32_t target) {
    if(range.empty || range.maximum < target)
        return false;
    return range.minimum - range.smallest < target;
}

struct SearchKey {
    std::uint32_t index;
    std::uint32_t minimum;
    std::uint32_t maximum;
    std::uint32_t smallest;
    bool empty;

    bool operator==(const SearchKey& other) const noexcept {
        return index == other.index
            && minimum == other.minimum
            && maximum == other.maximum
            && smallest == other.smallest
            && empty == other.empty;
    }
};

struct SearchHash {
    std::size_t operator()(const SearchKey& key) const noexcept {
        auto hash = static_cast<std::size_t>(key.index);
        hash = hash * 1315423911u + key.minimum;
        hash = hash * 1315423911u + key.maximum;
        hash = hash * 1315423911u + key.smallest;
        hash = hash * 1315423911u + static_cast<std::size_t>(key.empty);
        return hash;
    }
};

bool search_range(
    const protocol::SumDecision& decision,
    const std::vector<std::uint32_t>& remaining,
    const std::vector<std::uint32_t>& suffix_maximum,
    std::uint32_t position,
    Range range,
    std::unordered_set<SearchKey, SearchHash>& failed
) {
    if(range_complete(range, decision.target))
        return true;
    if(!range.empty && range.minimum - range.smallest >= decision.target)
        return false;
    if(range.maximum + suffix_maximum[position] < decision.target)
        return false;
    if(position == remaining.size())
        return false;

    const SearchKey key{
        position,
        range.minimum,
        std::min(range.maximum, decision.target),
        range.empty ? 0u : range.smallest,
        range.empty,
    };
    if(failed.find(key) != failed.end())
        return false;

    if(search_range(decision, remaining, suffix_maximum, position + 1, range, failed))
        return true;

    add(range, decision.cards[remaining[position]]);
    if(search_range(decision, remaining, suffix_maximum, position + 1, range, failed))
        return true;

    failed.insert(key);
    return false;
}

bool range_can_complete(
    const protocol::SumDecision& decision,
    const std::vector<std::uint32_t>& selected
) {
    auto range = selected_range(decision, selected);
    std::vector<std::uint32_t> remaining;
    remaining.reserve(decision.cards.size() - selected.size());
    for(std::uint32_t index = 0; index < decision.cards.size(); ++index) {
        if(!contains(selected, index))
            remaining.push_back(index);
    }

    std::vector<std::uint32_t> suffix_maximum(remaining.size() + 1, 0);
    for(std::size_t position = remaining.size(); position > 0; --position) {
        const auto card_values = values(decision.cards[remaining[position - 1]].value);
        suffix_maximum[position - 1] = suffix_maximum[position] + std::max(card_values[0], card_values[1]);
    }

    std::unordered_set<SearchKey, SearchHash> failed;
    return search_range(decision, remaining, suffix_maximum, 0, range, failed);
}

}

bool sum_complete(
    const protocol::SumDecision& decision,
    const std::vector<std::uint32_t>& selected
) {
    if(decision.mode == 0) {
        if(selected.size() < decision.min || selected.size() > decision.max)
            return false;
        return mandatory_sums(decision, selected).test(decision.target);
    }
    return range_complete(selected_range(decision, selected), decision.target);
}

bool sum_can_complete(
    const protocol::SumDecision& decision,
    const std::vector<std::uint32_t>& selected
) {
    return decision.mode == 0
        ? exact_can_complete(decision, selected)
        : range_can_complete(decision, selected);
}

}
