import argparse
from pathlib import Path

from ygo_gym import Deck, Engine
from ygo_gym.dataset import Dataset, DatasetWriter
from ygo_gym.task import Task


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path)
    parser.add_argument("--dataset", type=Path, default=Path("games.duckdb"))
    args = parser.parse_args()
    engine = Engine.from_checkout(args.root)
    deck = Deck(main=(69247929,) * 40)
    with engine.create_duel(deck, deck, seed=123) as duel:
        for _ in range(6):
            duel.step(0)
        replay = duel.replay()
    game_id = DatasetWriter(args.dataset, engine, task=Task(max_steps=6), snapshot_every=2).write(replay)
    with Dataset.open(args.dataset) as dataset:
        print("Saved boundaries:", [row["boundary"] for row in dataset.snapshots(game_id)])
        with dataset.restore(engine, game_id, 2) as restored:
            print("Restored dataset actions:", len(restored.actions))


if __name__ == "__main__":
    main()
