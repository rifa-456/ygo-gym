import pytest

from ygo_gym import Engine, Puzzle
from ygo_gym.dataset.initialization import Provenance
from ygo_gym.persistence import check_snapshot


@pytest.fixture(scope="module")
def expanded_engine(pytestconfig):
    assets = pytestconfig.rootpath / "third_party"
    cards, scripts = assets / "BabelCDB", assets / "CardScripts"
    return Engine(
        cards / "cards.cdb",
        (
            scripts,
            *(
                scripts / name
                for name in (
                    "official",
                    "unofficial",
                    "rush",
                    "skill",
                    "pre-errata",
                    "goat",
                    "pre-release",
                )
            ),
        ),
        additional_card_databases=tuple(
            cards / name
            for name in (
                "cards-unofficial.cdb",
                "cards-rush.cdb",
                "cards-skills.cdb",
                "cards-skills-unofficial.cdb",
            )
        ),
    )


@pytest.mark.parametrize(
    "name",
    [
        "GX Spirit Caller/1_Beginner/[GX_Spirit_Caller]B03_Oh_Jama.lua",
        "RUSH DUEL Dawn of the Battle Royale!!/XX Extra/[RUSH] Puzzle 01.lua",
    ],
)
def test_nonstandard_card_sets_load_without_changing_puzzle(expanded_engine, name):
    with Puzzle.builtin(name).start(expanded_engine, seed=1) as episode:
        assert episode.actions
        assert not episode.ended


def test_extra_databases_are_part_of_snapshot_compatibility(engine, expanded_engine):
    provenance = Provenance.capture(expanded_engine)
    assert len(expanded_engine.card_databases) == 5
    assert provenance.database_sha256 != Provenance.capture(engine).database_sha256
    with Puzzle.builtin("Duel Links/Naim_DuelLinks_1_10.lua").start(
        expanded_engine, seed=1
    ) as episode:
        data = episode.duel.serialize(provenance=provenance)
        assert check_snapshot(expanded_engine, data, provenance=provenance).compatible
        assert "database_sha256" in check_snapshot(engine, data).differences


@pytest.mark.parametrize("name", Puzzle.list_builtin())
def test_collection_starts_with_available_card_assets(expanded_engine, name):
    try:
        with Puzzle.builtin(name).start(expanded_engine, seed=42) as episode:
            assert episode.ended or episode.actions
    except RuntimeError as error:
        prefix = "card database has no entry for code "
        if prefix in str(error):
            code = int(str(error).split(prefix, 1)[1].split()[0])
            if 504700000 <= code < 504800000:
                pytest.xfail(
                    "upstream puzzle uses a legacy card ID absent from current BabelCDB"
                )
        raise
