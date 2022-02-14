import pytest
from pkg_resources import resource_filename

from p2a_impacts.resolver import resolve_rules
from p2a_impacts.utils import get_region


@pytest.mark.slow
@pytest.mark.parametrize(
    ("csv", "date_range", "region", "geoserver", "ensemble", "thredds"),
    [
        (
            resource_filename("tests", "data/rules-basic.csv"),
            "hist",
            "vancouver_island",
            "http://docker-dev01.pcic.uvic.ca:30123/geoserver/bc_regions/ows",
            "p2a_rules",
            True,
        ),
    ],
)
def test_resolve_rules_basic(
    populateddb,
    mock_thredds_url_root,
    mock_urls,
    csv,
    date_range,
    region,
    geoserver,
    ensemble,
    thredds,
):
    sesh = populateddb.session
    rules = resolve_rules(
        csv, date_range, get_region(region, geoserver), ensemble, sesh, thredds
    )
    expected_rules = {"rule_snow": True, "rule_hybrid": True, "rule_rain": True}
    assert rules == expected_rules


@pytest.mark.online
@pytest.mark.slow
@pytest.mark.parametrize(
    ("csv", "region", "geoserver", "ensemble", "thredds"),
    [
        (
            resource_filename("tests", "data/rules-multi-percentile.csv"),
            "vancouver_island",
            "http://docker-dev01.pcic.uvic.ca:30123/geoserver/bc_regions/ows",
            "p2a_rules",
            True,
        ),
    ],
)
@pytest.mark.parametrize("date_range", ["2050", "2080"])
def test_resolve_rules_multi_percentile(
    populateddb,
    mock_thredds_url_root,
    csv,
    date_range,
    region,
    geoserver,
    ensemble,
    thredds,
):
    sesh = populateddb.session
    rules = resolve_rules(
        csv, date_range, get_region(region, geoserver), ensemble, sesh, thredds
    )
    expected_rules = {
        "rule_future-snow": True,
        "rule_future-hybrid": True,
        "rule_future-rain": True,
    }
    assert rules == expected_rules


@pytest.mark.online
@pytest.mark.slow
@pytest.mark.parametrize(
    ("csv", "date_range", "region", "geoserver", "ensemble", "thredds"),
    [
        (
            resource_filename("tests", "data/rules-multi-var.csv"),
            "hist",
            "vancouver_island",
            "http://docker-dev01.pcic.uvic.ca:30123/geoserver/bc_regions/ows",
            "p2a_rules",
            True,
        ),
    ],
)
def test_resolve_rules_multi_var(
    populateddb,
    mock_thredds_url_root,
    csv,
    date_range,
    region,
    geoserver,
    ensemble,
    thredds,
):
    sesh = populateddb.session
    rules = resolve_rules(
        csv, date_range, get_region(region, geoserver), ensemble, sesh, thredds
    )
    expected_rules = {"rule_shm": 65.807}
    assert round(rules["rule_shm"], 3) == expected_rules["rule_shm"]
