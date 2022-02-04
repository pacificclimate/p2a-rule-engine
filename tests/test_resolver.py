import pytest
from pkg_resources import resource_filename

from p2a_impacts.resolver import resolve_rules
from p2a_impacts.utils import get_region


@pytest.mark.online
@pytest.mark.parametrize(
    ("csv", "date_range", "region", "geoserver", "ensemble", "thredds"),
    [
        (
            resource_filename("tests", "data/rules_small.csv"),
            "hist",
            "vancouver_island",
            "http://docker-dev01.pcic.uvic.ca:30123/geoserver/bc_regions/ows",
            "p2a_rules",
            True,
        ),
    ],
)
def test_resolve_rules(
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
    expected_rules = {"rule_snow": True, "rule_hybrid": True, "rule_rain": True}
    assert rules == expected_rules
