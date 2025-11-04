import pytest
from importlib.resources import files

from p2a_impacts.resolver import resolve_rules
from p2a_impacts.utils import get_region
import os
import requests
import mock
import netCDF4
from netCDF4 import Dataset
from .mock_data import tasmin_data, tasmax_data


def mock_opendap_request(path, mode="r"):
    basename = os.path.basename(path)
    test_data_dir = files("tests") / "data"
    file_path = test_data_dir / basename
    if not file_path.exists():
        raise FileNotFoundError(f"File not found in mock: {file_path}")
    return Dataset(str(file_path), mode)


@mock.patch("netCDF4.Dataset", side_effect=mock_opendap_request)
def test_mock_opendap_request(mock_opendap_request, mock_thredds_url_root):
    base_path_tasmin = "/storage/data/climate/downscale/MBCn/PCIC-Blend/Derived/seasonal/climatologies/tasmin_seasonal_average_Climatology_PCIC-Blend_Observations_v1_1981-2010.nc"
    dods_path_tasmin = os.getenv("THREDDS_URL_ROOT") + base_path_tasmin
    tasmin = netCDF4.Dataset(dods_path_tasmin)
    base_path_tasmax = "/storage/data/climate/downscale/MBCn/PCIC-Blend/Derived/seasonal/climatologies/tasmax_seasonal_average_Climatology_PCIC-Blend_Observations_v1_1981-2010.nc"
    dods_path_tasmax = os.getenv("THREDDS_URL_ROOT") + base_path_tasmax
    tasmax = netCDF4.Dataset(dods_path_tasmax)
    assert mock_opendap_request.call_count == 2


@pytest.mark.online
@pytest.mark.slow
@pytest.mark.parametrize(
    ("csv", "date_range", "region", "geoserver", "ensemble", "thredds"),
    [
        (
            str((files("tests") / "data/rules-basic.csv").resolve()),
            "hist",
            "vancouver_island",
            "https://beehive.pacificclimate.org/plan2adapt/bc_regions/ows",
            "p2a_rules_cmip6_mbcn",
            True,
        ),
    ],
)
@mock.patch("ce.api.util.Dataset", side_effect=mock_opendap_request)
def test_resolve_rules_basic(
    mock_opendap_request,
    populateddb_thredds,
    mock_thredds_url_root,
    mock_urls,
    csv,
    date_range,
    region,
    geoserver,
    ensemble,
    thredds,
):
    sesh = populateddb_thredds
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
            str((files("tests") / "data/rules-multi-percentile.csv").resolve()),
            "vancouver_island",
            "https://beehive.pacificclimate.org/plan2adapt/bc_regions/ows",
            "p2a_rules_cmip6_mbcn",
            True,
        ),
    ],
)
@pytest.mark.parametrize("date_range", ["2050", "2080"])
def test_resolve_rules_multi_percentile(
    populateddb_thredds,
    mock_thredds_url_root,
    csv,
    date_range,
    region,
    geoserver,
    ensemble,
    thredds,
    monkeypatch,
):
    sesh = populateddb_thredds
    import p2a_impacts.fetch_data as fetch_data

    monkeypatch.setattr(fetch_data, "USE_RCP85", True)
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
            str((files("tests") / "data/rules-multi-var.csv").resolve()),
            "hist",
            "vancouver_island",
            "https://beehive.pacificclimate.org/plan2adapt/bc_regions/ows",
            "p2a_rules_cmip6_mbcn",
            True,
        ),
    ],
)
def test_resolve_rules_multi_var(
    populateddb_thredds,
    mock_thredds_url_root,
    csv,
    date_range,
    region,
    geoserver,
    ensemble,
    thredds,
):
    sesh = populateddb_thredds
    rules = resolve_rules(
        csv, date_range, get_region(region, geoserver), ensemble, sesh, thredds
    )
    expected_rules = {"rule_shm": 53.71}
    assert round(rules["rule_shm"], 3) == expected_rules["rule_shm"]


@pytest.mark.parametrize(
    ("csv", "date_range", "region", "geoserver", "ensemble", "thredds"),
    [
        (
            str((files("tests") / "data/rules-basic.csv").resolve()),
            "hist",
            "vancouver_island",
            "https://beehive.pacificclimate.org/plan2adapt/bc_regions/ows",
            "p2a_rules_cmip6_mbcn",
            False,
        ),
    ],
)
def test_resolve_rules_local(
    populateddb_local,
    mock_urls,
    csv,
    date_range,
    region,
    geoserver,
    ensemble,
    thredds,
):
    sesh = populateddb_local
    rules = resolve_rules(
        csv, date_range, get_region(region, geoserver), ensemble, sesh, thredds
    )
    expected_rules = {"rule_snow": True, "rule_hybrid": True, "rule_rain": True}
    assert rules == expected_rules


def test_mock_urls(mock_thredds_url_root, mock_urls, requests_mock):
    base_path_tasmin = "/storage/data/climate/downscale/MBCn/PCIC-Blend/Derived/monthly/climatologies/tasmin_seasonal_average_Climatology_PCIC-Blend_Observations_v1_1981-2010.nc"
    base_path_tasmax = "/storage/data/climate/downscale/MBCn/PCIC-Blend/Derived/monthly/climatologies/tasmax_seasonal_average_Climatology_PCIC-Blend_Observations_v1_1981-2010.nc"

    fileserver_base_url = "http://marble-dev01.pcic.uvic.ca/twitcher/ows/proxy/thredds/fileServer/datasets"
    fileserver_path_tasmin = fileserver_base_url + base_path_tasmin
    fileserver_path_tasmax = fileserver_base_url + base_path_tasmax

    requests_mock.get(fileserver_path_tasmin, content=tasmin_data)
    requests_mock.get(fileserver_path_tasmax, content=tasmax_data)

    assert requests.get(fileserver_path_tasmin).content == tasmin_data
    assert requests.get(fileserver_path_tasmax).content == tasmax_data
