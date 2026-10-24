"""Record a synthetic-deck duel from its replay and relabel it, using the checkout's pinned assets."""

import argparse
from pathlib import Path

from ygo_gym import Deck, Engine, Provenance
from ygo_gym.action import ActionKind
from ygo_gym.dataset import Dataset, DatasetWriter
from ygo_gym.task import Task


def choose(game) -> int:
    for kind in (
        ActionKind.END_PHASE,
        ActionKind.PASS,
        ActionKind.CONFIRM,
        ActionKind.SELECT_CARD,
        ActionKind.SELECT_ZONE,
        ActionKind.NO,
    ):
        for index, action in enumerate(game.actions):
            if action.kind == kind:
                return index
    return 0


def life_point_reward(transition, context):
    before = transition.before["state"]["global_state"]["life_points"]
    after = transition.after["state"]["global_state"]["life_points"]
    delta = ((after[0] - before[0]) - (after[1] - before[1])) / context.config["scale"]
    return delta, -delta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--derived", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=20)
    args = parser.parse_args()
    if args.steps < 1:
        parser.error("--steps must be positive")
    engine = Engine.from_checkout(args.root)
    provenance = Provenance.capture(engine)
    deck = Deck((69247929,) * 40)
    with engine.create_duel(deck, deck, seed=123) as duel:
        for _ in range(args.steps):
            if duel.terminated:
                break
            duel.step(choose(duel))
        replay = duel.replay()
    writer = DatasetWriter(args.output, engine, task=Task(max_steps=args.steps), provenance=provenance, append=False)
    game_id = writer.write(replay)
    with Dataset.open(args.output) as dataset:
        report = dataset.validate_replay(engine, game_id, provenance=provenance)
        if not report.compatible:
            raise RuntimeError(report)
        task = Task(
            name="life-point-delta",
            config={"scale": 8000},
            reward=life_point_reward,
            max_steps=max(1, args.steps // 2),
        )
        dataset.relabel(task).save(args.derived, append=False)
        print(f"Recorded {report.checked_steps} validated steps in {args.output}")
        print(f"Saved relabelled steps in {args.derived}; the original file is unchanged")


if __name__ == "__main__":
    main()
