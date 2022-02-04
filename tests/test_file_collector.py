import pytest
from scripts.file_collector import get_paths_by_var
from p2a_impacts.utils import setup_logging


# Most of file_collector's functionality is covered by test_fetch_data.py
@pytest.mark.parametrize(
    ("ensemble", "date", "area", "variables"),
    (
        [
            "p2a_rules",
            "2080",
            {
                "the_geom": """POLYGON((-122.70904541015625 49.31438004800689,
            -122.92327880859375 49.35733376286064,-123.14849853515625
            49.410973199695846,-123.34625244140625
            49.30721745093609,-123.36273193359375
            49.18170338770662,-123.20343017578125
            49.005447494058096,-122.44537353515625
            49.023461463214126,-122.46734619140625
            49.13500260581219,-122.50579833984375
            49.31079887964633,-122.70904541015625 49.31438004800689))"""
            },
            {
                "temp_djf_iamean_s0p_hist": {
                    "variable": "temp",
                    "time_of_year": "djf",
                    "temporal": "iamean",
                    "spatial": "s0p",
                    "percentile": "hist",
                },
            },
        ],
    ),
)
def test_get_paths_by_var(populateddb, ensemble, date, area, variables):
    sesh = populateddb.session
    logger = setup_logging("ERROR")

    for name, values in variables.items():
        paths = get_paths_by_var(sesh, values, ensemble, date, area, False, logger)

    for path in paths:
        assert "/ce/tests/data/" in path or "/storage/data/" in path
