from ..state import Location


def render(setup) -> str:
    flags = "DUEL_MODE_MR5"
    if setup.allow_first_turn_attack:
        flags += " | DUEL_ATTACK_FIRST_TURN"
    lines = [f"Debug.ReloadFieldBegin({flags}, 0, true)"]
    for player, config in enumerate(setup.players):
        lines.append(
            f"Debug.SetPlayerInfo({player}, {config.life_points}, 0, {config.draw_count})"
        )
    cards = sorted(
        setup.cards, key=lambda c: (c.controller, int(c.location), c.sequence)
    )
    lines.append("local card")
    lines.append("local placed = {}")
    for index, card in enumerate(cards, 1):
        sequence = 0 if card.location == Location.DECK else card.sequence
        lines.append(
            f"card = Debug.AddCard({card.code}, {card.owner}, {card.controller}, "
            f"{int(card.location)}, {sequence}, {int(card.position)}, "
            f"{str(card.summon_complete).lower()})"
        )
        lines.append('assert(card, "card placement failed")')
        lines.append(
            f"placed[{index}] = {{card, {int(card.location)}, {card.sequence}}}"
        )
    lines.extend(
        (
            "for _, placement in ipairs(placed) do",
            'assert(placement[1]:GetSequence() == placement[3] and placement[1]:IsLocation(placement[2]), "zone order cannot be represented by this setup")',
            "end",
            "Debug.ReloadFieldEnd()",
        )
    )
    for phase, code in (
        ("PHASE_DRAW", "EFFECT_SKIP_DP"),
        ("PHASE_STANDBY", "EFFECT_SKIP_SP"),
    ):
        lines.extend(
            (
                "do",
                "local effect = Effect.GlobalEffect()",
                "effect:SetType(EFFECT_TYPE_FIELD)",
                "effect:SetProperty(EFFECT_FLAG_PLAYER_TARGET)",
                f"effect:SetCode({code})",
                "effect:SetTargetRange(1, 0)",
                f"effect:SetReset(RESET_PHASE | {phase}, 1)",
                "Duel.RegisterEffect(effect, 0)",
                "end",
            )
        )
    return "\n".join(lines) + "\n"
