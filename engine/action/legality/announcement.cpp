#include "action/legality/legality.h"

#include <algorithm>
#include <cstdint>
#include <stack>

#include "ygopro-core/card.h"
#include "ygopro-core/ocgapi_constants.h"

namespace ygo_gym::action {
namespace {

bool declarable(const CardDefinition& card, const std::vector<std::uint64_t>& opcodes) {
    std::stack<std::int64_t> stack;
    bool allow_aliases = false;
    bool allow_tokens = false;

    const auto binary = [&stack](auto operation) {
        if(stack.size() < 2)
            return;
        const auto rhs = stack.top();
        stack.pop();
        const auto lhs = stack.top();
        stack.pop();
        stack.push(operation(lhs, rhs));
    };
    const auto unary = [&stack](auto operation) {
        if(stack.empty())
            return;
        const auto value = stack.top();
        stack.pop();
        stack.push(operation(value));
    };

    for(const auto opcode : opcodes) {
        switch(opcode) {
        case OPCODE_ADD: binary([](auto lhs, auto rhs) { return lhs + rhs; }); break;
        case OPCODE_SUB: binary([](auto lhs, auto rhs) { return lhs - rhs; }); break;
        case OPCODE_MUL: binary([](auto lhs, auto rhs) { return lhs * rhs; }); break;
        case OPCODE_DIV:
            if(stack.size() >= 2 && stack.top() != 0)
                binary([](auto lhs, auto rhs) { return lhs / rhs; });
            break;
        case OPCODE_AND: binary([](auto lhs, auto rhs) { return static_cast<std::int64_t>(lhs && rhs); }); break;
        case OPCODE_OR: binary([](auto lhs, auto rhs) { return static_cast<std::int64_t>(lhs || rhs); }); break;
        case OPCODE_NEG: unary([](auto value) { return -value; }); break;
        case OPCODE_NOT: unary([](auto value) { return static_cast<std::int64_t>(!value); }); break;
        case OPCODE_BAND: binary([](auto lhs, auto rhs) { return lhs & rhs; }); break;
        case OPCODE_BOR: binary([](auto lhs, auto rhs) { return lhs | rhs; }); break;
        case OPCODE_BXOR: binary([](auto lhs, auto rhs) { return lhs ^ rhs; }); break;
        case OPCODE_BNOT: unary([](auto value) { return ~value; }); break;
        case OPCODE_LSHIFT: binary([](auto lhs, auto rhs) { return lhs << rhs; }); break;
        case OPCODE_RSHIFT: binary([](auto lhs, auto rhs) { return lhs >> rhs; }); break;
        case OPCODE_ISCODE: unary([&card](auto value) { return static_cast<std::int64_t>(card.code == static_cast<std::uint32_t>(value)); }); break;
        case OPCODE_ISTYPE: unary([&card](auto value) { return static_cast<std::int64_t>(card.type & value); }); break;
        case OPCODE_ISRACE: unary([&card](auto value) { return static_cast<std::int64_t>(card.race & value); }); break;
        case OPCODE_ISATTRIBUTE: unary([&card](auto value) { return static_cast<std::int64_t>(card.attribute & value); }); break;
        case OPCODE_GETCODE: stack.push(card.code); break;
        case OPCODE_GETTYPE: stack.push(card.type); break;
        case OPCODE_GETRACE: stack.push(static_cast<std::int64_t>(card.race)); break;
        case OPCODE_GETATTRIBUTE: stack.push(card.attribute); break;
        case OPCODE_ISSETCARD: {
            if(stack.empty())
                break;
            const auto set_code = static_cast<std::uint16_t>(stack.top());
            stack.pop();
            const auto type = static_cast<std::uint16_t>(set_code & 0x0fff);
            const auto subtype = static_cast<std::uint16_t>(set_code & 0xf000);
            bool matches = false;
            for(const auto setcode : card.setcodes) {
                if(setcode == 0)
                    continue;
                if((setcode & 0x0fff) == type && (setcode & 0xf000 & subtype) == subtype) {
                    matches = true;
                    break;
                }
            }
            stack.push(matches);
            break;
        }
        case OPCODE_ALLOW_ALIASES: allow_aliases = true; break;
        case OPCODE_ALLOW_TOKENS: allow_tokens = true; break;
        default: stack.push(static_cast<std::int64_t>(opcode)); break;
        }
    }

    if(stack.size() != 1 || stack.top() == 0)
        return false;
    if(card.code == CARD_MARINE_DOLPHIN || card.code == CARD_TWINKLE_MOSS)
        return true;
    const bool token = (card.type & (TYPE_MONSTER | TYPE_TOKEN)) == (TYPE_MONSTER | TYPE_TOKEN);
    return (allow_aliases || card.alias == 0) && (allow_tokens || !token);
}

}

std::vector<std::uint32_t> declarable_cards(
    const EngineState& engine,
    const protocol::AnnounceCardDecision& decision
) {
    std::vector<std::uint32_t> cards;
    cards.reserve(engine.cards.size());
    for(const auto& [code, definition] : engine.cards) {
        if(declarable(definition, decision.opcodes))
            cards.push_back(code);
    }
    std::sort(cards.begin(), cards.end());
    return cards;
}

}
