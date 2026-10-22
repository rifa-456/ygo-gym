import argparse
from pathlib import Path

from ygo_gym import Deck, Engine
from ygo_gym.dataset import Dataset, Recorder
from ygo_gym.task import Task


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path)
    parser.add_argument("--snapshot", type=Path, default=Path("duel.ygos"))
    parser.add_argument("--dataset", type=Path, default=Path("games.duckdb"))
    args = parser.parse_args()
    engine = Engine.from_checkout(args.root)
    deck = Deck(main=(69247929,) * 40)
    with engine.create_duel(deck, deck, seed=123) as duel:
        duel.step(0)
        duel.save(args.snapshot)
    with engine.load(args.snapshot) as restored:
        print("Restored player:", restored.current_player)
        print("Legal actions:", len(restored.actions))
    with Recorder.create(engine, deck, deck, seed=123, task=Task(max_steps=6)) as recorder:
        while not recorder.ended:
            recorder.step(0)
        recorder.save(args.dataset, snapshot_every=2)
        game_id = recorder.game_id
    with Dataset.open(args.dataset) as dataset:
        print("Saved boundaries:", [row["boundary"] for row in dataset.snapshots(game_id)])
        with dataset.restore(engine, game_id, 2) as restored:
            print("Restored dataset actions:", len(restored.actions))


if __name__ == "__main__":
    main()
