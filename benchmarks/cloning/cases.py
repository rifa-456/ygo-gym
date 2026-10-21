import argparse
from dataclasses import dataclass
from itertools import product


SCENARIOS = ("simple", "developed", "suspended")
MODES = ("exact", "seeded", "fresh")


def positive(value: str) -> int:
    result = int(value)
    if result < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return result


def seed(value: str) -> int:
    result = int(value)
    if not 0 <= result <= 2**64 - 1:
        raise argparse.ArgumentTypeError("must fit in uint64")
    return result


@dataclass(frozen=True, slots=True)
class Case:
    scenario: str
    mode: str
    scenario_seed: int
    clone_seed: int

    @property
    def name(self) -> str:
        return f"{self.scenario}/{self.mode}"

    @property
    def clone_options(self) -> dict:
        if self.mode == "exact":
            return {"preserve_rng": True}
        if self.mode == "seeded":
            return {"seed": self.clone_seed}
        return {}


def add_arguments(parser) -> None:
    parser.add_argument("--scenario", choices=SCENARIOS)
    parser.add_argument("--mode", choices=MODES)
    parser.add_argument("--scenario-seed", type=seed, default=123, help="initial duel seed")
    parser.add_argument("--clone-seed", type=seed, default=42, help="future RNG seed used only in seeded mode")
    parser.add_argument("--build-label", default="unspecified")


def selected(args):
    scenarios = (args.scenario,) if args.scenario else SCENARIOS
    modes = (args.mode,) if args.mode else MODES
    return [Case(scenario, mode, args.scenario_seed, args.clone_seed)
            for scenario, mode in product(scenarios, modes)]


def command_arguments(case: Case, build_label: str) -> list[str]:
    return ["--scenario", case.scenario, "--mode", case.mode,
            "--scenario-seed", str(case.scenario_seed), "--clone-seed", str(case.clone_seed),
            "--build-label", build_label]
