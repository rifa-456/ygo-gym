from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from ..task import Task, TaskResult, TaskSession, Transition


@dataclass(frozen=True, slots=True)
class Evaluation:
    dataset: object
    task: Task

    def steps(self, game_id: str | None = None):
        games = [self.dataset.game(game_id)] if game_id is not None else self.dataset.games()
        for game in games:
            session = TaskSession(self.task, game["game_id"])
            for row in self.dataset.steps(game["game_id"]):
                transition = Transition(
                    **{key: deepcopy(row[key]) for key in Transition.__dataclass_fields__}
                )
                row["result"] = session.evaluate(transition).as_record()
                yield row
                if session.result.ended:
                    break

    def _game(self, game: dict, steps: list) -> dict:
        game["task"] = self.task.describe()
        game["step_count"] = len(steps)
        if steps:
            game["result"] = steps[-1]["result"]
            game["outcome"] = steps[-1]["after"]["outcome"]
        else:
            frame = game["initial"]
            game["result"] = TaskResult(
                tuple(frame["engine_rewards"]),
                frame["engine_terminated"],
                False,
                "duel_end" if frame["engine_terminated"] else None,
            ).as_record()
            game["outcome"] = frame["outcome"]
        ended = game["result"]["terminated"] or game["result"]["truncated"]
        game["recording_status"] = "complete" if ended else "partial"
        return game

    def game(self, game_id: str) -> dict:
        return self._game(self.dataset.game(game_id), list(self.steps(game_id)))

    def save(self, path: str | Path, *, append: bool = True):
        if Path(path).resolve() == self.dataset.path:
            raise ValueError("save an evaluation to a different dataset; original labels are retained")
        from .storage.writing import save_many

        def episodes():
            for game in self.dataset.games():
                rows = list(self.steps(game["game_id"]))
                yield self._game(game, rows), rows

        save_many(path, episodes(), append=append)
