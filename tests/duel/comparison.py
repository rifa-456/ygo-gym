from ygo_gym import Duel, Outcome, action, event, protocol, state


_FIELDS: dict[type, tuple[str, ...]] = {
    Outcome: ("winner", "reason", "rewards"),
    action.SimpleAction: ('kind',),
    action.CardAction: ('kind', 'card'),
    action.EffectAction: ('kind', 'card', 'description', 'client_mode'),
    action.AttackAction: ('kind', 'card', 'direct'),
    action.TributeAction: ('kind', 'card', 'value'),
    action.SumAction: ('kind', 'card', 'value'),
    action.ZoneAction: ('kind', 'zone'),
    action.PositionAction: ('kind', 'position'),
    action.OptionAction: ('kind', 'index', 'description'),
    action.CounterAction: ('kind', 'card', 'available', 'count'),
    action.RaceAction: ('kind', 'race'),
    action.AttributeAction: ('kind', 'attribute'),
    action.CardCodeAction: ('kind', 'code'),
    action.NumberAction: ('kind', 'index', 'number'),
    action.RpsAction: ('kind', 'choice'),
    protocol.AnnounceRaceDecision: ('kind', 'player', 'count', 'available'),
    protocol.AnnounceAttributeDecision: ('kind', 'player', 'count', 'available'),
    protocol.AnnounceCardDecision: ('kind', 'player', 'opcodes'),
    protocol.AnnounceNumberDecision: ('kind', 'player', 'options'),
    protocol.RockPaperScissorsDecision: ('kind', 'player'),
    protocol.BattleDecision: ('kind', 'player', 'activatable', 'attackable', 'can_main_phase_2', 'can_end_phase'),
    protocol.IdleDecision: ('kind', 'player', 'summonable', 'special_summonable', 'repositionable', 'monster_settable', 'spell_trap_settable', 'activatable', 'can_battle_phase', 'can_end_phase', 'can_shuffle_hand'),
    protocol.EffectYesNoDecision: ('kind', 'player', 'card', 'description'),
    protocol.YesNoDecision: ('kind', 'player', 'description'),
    protocol.OptionDecision: ('kind', 'player', 'options'),
    protocol.ChainDecision: ('kind', 'player', 'special_count', 'forced', 'hint_timing', 'opponent_hint_timing', 'options'),
    protocol.CoreResponse: ('kind', 'bytes'),
    protocol.CardRef: ('code', 'controller', 'location', 'sequence', 'position'),
    protocol.EffectRef: ('card', 'description', 'client_mode'),
    protocol.AttackRef: ('card', 'direct'),
    protocol.TributeRef: ('card', 'value'),
    protocol.CounterRef: ('card', 'available'),
    protocol.SumRef: ('card', 'value'),
    protocol.ZoneRef: ('player', 'location', 'sequence'),
    protocol.CardDecision: ('kind', 'player', 'cancelable', 'min', 'max', 'cards'),
    protocol.PlaceDecision: ('kind', 'player', 'count', 'unavailable', 'disable_field'),
    protocol.PositionDecision: ('kind', 'player', 'card_code', 'positions'),
    protocol.TributeDecision: ('kind', 'player', 'cancelable', 'min', 'max', 'cards'),
    protocol.CounterDecision: ('kind', 'player', 'counter_type', 'count', 'cards'),
    protocol.SumDecision: ('kind', 'player', 'mode', 'target', 'min', 'max', 'required', 'cards'),
    protocol.SortDecision: ('kind', 'player', 'chain', 'cards'),
    protocol.UnselectCardDecision: ('kind', 'player', 'finishable', 'cancelable', 'min', 'max', 'selectable', 'unselectable'),
    state.GlobalState: ('turn_player', 'decision_player', 'turn_count', 'phase', 'life_points'),
    state.CardProperties: ('alias', 'type', 'attribute', 'race'),
    state.MonsterState: ('level', 'rank', 'attack', 'defense', 'base_attack', 'base_defense'),
    state.PendulumState: ('left_scale', 'right_scale'),
    state.LinkState: ('rating', 'markers'),
    state.ZoneCount: ('player', 'location', 'count'),
    state.CounterState: ('card', 'type', 'count'),
    state.RelationState: ('kind', 'source', 'target', 'sequence'),
    state.ChainState: ('index', 'card', 'triggering_player', 'triggering_controller', 'triggering_location', 'triggering_sequence', 'description'),
    state.PlayerState: ('life_points', 'starting_life_points', 'starting_hand_size', 'draw_count', 'used_locations', 'disabled_locations', 'faceup_extra_count'),
    state.StateCard: ('id', 'code', 'owner', 'controller', 'location', 'sequence', 'position', 'properties', 'monster', 'pendulum', 'link'),
    state.State: ('global_state', 'duel_options', 'cards', 'counters', 'relations', 'chain', 'pending_actions', 'events'),
    state.Card: ('id', 'code', 'owner', 'controller', 'location', 'sequence', 'position', 'properties', 'monster', 'pendulum', 'link'),
    state.Observation: ('viewer', 'global_state', 'cards', 'zone_counts', 'counters', 'relations', 'chain', 'pending_actions', 'events'),
    event.DeckReverseEvent: (),
    event.LifePointEvent: ('player', 'amount', 'kind'),
    event.CounterEvent: ('card', 'type', 'change'),
    event.RelationEvent: ('kind', 'source', 'target'),
    event.AttackEvent: ('attacker', 'target'),
    event.BattleEvent: ('attacker', 'attacker_attack', 'attacker_defense', 'attacker_destroyed', 'target', 'target_attack', 'target_defense', 'target_destroyed'),
    event.RandomEvent: ('player', 'kind', 'results'),
    event.DamageStepEvent: ('stage',),
    event.GraveDeckSwapEvent: ('player',),
    event.WinEvent: ('winner', 'reason'),
    event.EventLocation: ('controller', 'location', 'sequence', 'position'),
    event.EventCard: ('id', 'code', 'current_card'),
    event.TurnEvent: ('player',),
    event.PhaseEvent: ('phase',),
    event.ShuffleEvent: ('player', 'location'),
    event.RevealEvent: ('card',),
    event.DrawEvent: ('player', 'card'),
    event.MoveEvent: ('card', 'previous', 'current', 'reason'),
    event.PositionEvent: ('card', 'controller', 'location', 'sequence', 'previous_position', 'position'),
    event.SetEvent: ('card',),
    event.SummonEvent: ('card', 'player', 'kind', 'stage'),
    event.ChainEvent: ('stage', 'card', 'player', 'description', 'chain_index'),
}


def values(value: object) -> object:
    if value is None or isinstance(value, (bool, int, float, str, bytes)):
        return value
    if hasattr(type(value), "__members__"):
        return type(value).__name__, value.name
    if isinstance(value, event.EventBatch):
        return "EventBatch", values(value.cards), tuple(map(values, value))
    if isinstance(value, (list, tuple, state.CardCollection, state.StateCardCollection, event.EventCardCollection)):
        return tuple(map(values, value))
    fields = _FIELDS.get(type(value))
    if fields is None:
        raise TypeError(f"no comparison schema for {type(value)}")
    return type(value).__name__, tuple((name, values(getattr(value, name))) for name in fields)


def observation(obs: state.Observation) -> tuple:
    return values(obs), tuple(tuple(obs.chain_targets(i)) for i in range(len(obs.chain)))


def full_state(full: state.State) -> tuple:
    locations = (
        state.Location.DECK, state.Location.HAND, state.Location.MONSTER_ZONE,
        state.Location.SPELL_TRAP_ZONE, state.Location.GRAVEYARD,
        state.Location.BANISHED, state.Location.EXTRA_DECK,
    )
    return (
        values(full),
        tuple(values(full.player(player)) for player in (0, 1)),
        tuple(tuple(full.zone(player, location)) for player in (0, 1) for location in locations),
        tuple(tuple(full.chain_targets(i)) for i in range(len(full.chain))),
    )


def duel(duel: Duel) -> tuple:
    return (
        duel.status, duel.current_player, duel.terminated, values(duel.outcome),
        duel.rewards, duel.message_buffer, values(duel.decision),
        values(duel.actions), values(duel.pending_actions),
        observation(duel.observe(0)), observation(duel.observe(1)), full_state(duel.state()),
    )


def choose(duel: Duel, *kinds: action.ActionKind) -> int:
    for kind in kinds:
        for index, candidate in enumerate(duel.actions):
            if candidate.kind == kind:
                return index
    raise AssertionError(f"none of {kinds} in {[a.kind for a in duel.actions]}")
