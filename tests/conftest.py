import pytest
import py.path
import tempfile
from ce import get_app
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from datetime import datetime
from importlib.resources import files
from dateutil.relativedelta import relativedelta

from modelmeta.v2 import (
    metadata,
    Ensemble,
    Emission,
    Model,
    Run,
    VariableAlias,
    Grid,
    Time,
    TimeSet,
    ClimatologicalTime,
    DataFile,
    DataFileVariableGridded,
)
from flask_sqlalchemy import SQLAlchemy

from .mock_data import geoserver_data, tasmin_data, tasmax_data


# Functions to create data for mock databases


def create_modelmeta_objects():
    """Create modelmeta objects used for both mock databases."""

    objects = {}

    # Ensembles

    p2a_rules = Ensemble(name="p2a_rules", version=1.0, changes="", description="")
    ensembles = [
        p2a_rules,
    ]
    objects["ensembles"] = ensembles

    # Emissions

    historical = Emission(short_name="historical")
    historical_rcp85 = Emission(short_name="historical,rcp85")

    # Runs

    run1 = Run(name="r1i1p1", emission=historical)
    run2 = Run(name="r1i1p1", emission=historical_rcp85)
    objects["run1"] = run1
    objects["run2"] = run2

    # Models
    canesm2 = Model(short_name="CanESM2", type="GCM", runs=[run2], organization="")
    pcic_blend = Model(
        short_name="PCIC_BLEND_v1", type="GCM", runs=[run1], organization=""
    )

    objects["canesm2"] = canesm2
    objects["pcic_blend"] = pcic_blend

    # VariableAliases

    # PCIC Blend
    tasmin_blend = VariableAlias(
        long_name="Seasonal Average Minimum Temperature",
        standard_name="Seasonal Average Minimum Temperature",
        units="degC",
    )
    tasmax_blend = VariableAlias(
        long_name="Seasonal Average Maximum Temperature",
        standard_name="Seasonal Average Maximum Temperature",
        units="degC",
    )

    # CanESM2
    tasmin_canesm2 = VariableAlias(
        long_name="Daily Minimum Temperature",
        standard_name="air_temperature",
        units="degC",
    )
    tasmax_canesm2 = VariableAlias(
        long_name="Daily Maximum Temperature",
        standard_name="air_temperature",
        units="degC",
    )

    pr = VariableAlias(
        long_name="Precipitation",
        standard_name="precipitation_flux",
        units="kg d-1 m-2",
    )
    flow_direction = VariableAlias(
        long_name="Flow Direction",
        standard_name="flow_direction",
        units="1",
    )
    variable_aliases_blend = [tasmin_blend, tasmax_blend, pr, flow_direction]
    variable_aliases_canesm2 = [tasmin_canesm2, tasmax_canesm2, pr, flow_direction]

    objects["variable_aliases_blend"] = variable_aliases_blend
    objects["variable_aliases_canesm2"] = variable_aliases_canesm2

    # Grids

    grid_pcic_blend = Grid(
        name="Canada ANUSPLINE",
        xc_grid_step=0.0833333,
        yc_grid_step=0.0833333,
        xc_origin=-140.958,
        yc_origin=41.0417,
        xc_count=1068,
        yc_count=510,
        xc_units="degrees_east",
        yc_units="degrees_north",
        evenly_spaced_y=True,
    )
    grids = [grid_pcic_blend]
    objects["grids"] = grids

    return objects


def make_data_file(
    filename=None,
    run=None,
):
    if not filename.startswith("/"):
        filename = str(files("tests") / "data" / filename)
    return DataFile(
        filename=filename,
        unique_id=filename,
        first_1mib_md5sum="xxxx",
        x_dim_name="lon",
        y_dim_name="lat",
        index_time=datetime.utcnow(),
        run=run,
    )


def make_data_file_variable(
    file,
    cell_methods,
    variable_aliases,
    var_name=None,
    grid=None,
):
    (tasmin, tasmax, pr, flow_direction) = variable_aliases[:]
    var_name_to_alias = {
        "tasmin": tasmin,
        "tasmax": tasmax,
        "pr": pr,
        "flow_direction": flow_direction,
    }[var_name]

    return DataFileVariableGridded(
        file=file,
        netcdf_variable_name=var_name,
        range_min=0,
        range_max=50,
        variable_alias=var_name_to_alias,
        grid=grid,
        variable_cell_methods=cell_methods,
    )


# Fixtures


@pytest.fixture
def mock_thredds_url_root(monkeypatch):
    monkeypatch.setenv(
        "THREDDS_URL_ROOT",
        "http://marble-dev01.pcic.uvic.ca/twitcher/ows/proxy/thredds/dodsC/datasets",
    )


@pytest.fixture(scope="function")
def ce_response():
    return {
        "test_period_20200101-20491230": {"mean": 1, "min": 0, "max": 2},
        "test_period_20400101-20691231": {"mean": 3, "min": 1, "max": 5},
        "test_period_20700101-20991231": {"mean": 5, "min": 0, "max": 10},
    }


@pytest.fixture()
def sessiondir(
    request,
):
    dir = py.path.local(tempfile.mkdtemp())
    request.addfinalizer(lambda: dir.remove(rec=1))
    return dir


@pytest.fixture()
def dsn(
    sessiondir,
):
    return f"sqlite:///{sessiondir.join('test.sqlite').realpath()}"


@pytest.fixture()
def app(dsn):
    app = get_app(
        config={
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": dsn,
            "SQLALCHEMY_ECHO": False,
        }
    )
    return app


@pytest.fixture
def cleandb(
    app,
):
    engine = create_engine(
        app.config["SQLALCHEMY_DATABASE_URI"], echo=app.config["SQLALCHEMY_ECHO"]
    )
    metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def populateddb_thredds(
    cleandb,
):
    """Create mock database only containing data files from THREDDS."""

    populateable_db = cleandb
    sesh = populateable_db
    objects = create_modelmeta_objects()
    p2a_rules = objects["ensembles"][0]
    grid_pcic_blend = objects["grids"][0]

    models = [objects["pcic_blend"], objects["canesm2"]]

    # Data files
    storage_root_pcic_blend_sea = "/storage/data/climate/downscale/MBCn/PCIC-Blend/Derived/seasonal/climatologies/"
    storage_root_pcic_blend_mon = (
        "/storage/data/climate/downscale/MBCn/PCIC-Blend/Derived/monthly/climatologies/"
    )
    storage_root_canesm2 = "/storage/data/projects/comp_support/climate_explorer_data_prep/climatological_means/downscale/output/"
    canesm2_tasmin_root = storage_root_canesm2 + "2433/"
    canesm2_tasmax_root = storage_root_canesm2 + "2495/"

    df_pcic_blend_tasmin_seasonal = make_data_file(
        filename=storage_root_pcic_blend_sea
        + "tasmin_seasonal_average_Climatology_PCIC-Blend_Observations_v1_1981-2010.nc",
        run=objects["run1"],
    )
    df_pcic_blend_tasmax_seasonal = make_data_file(
        filename=storage_root_pcic_blend_sea
        + "tasmax_seasonal_average_Climatology_PCIC-Blend_Observations_v1_1981-2010.nc",
        run=objects["run1"],
    )
    df_pcic_blend_pr_seasonal = make_data_file(
        filename=storage_root_pcic_blend_sea
        + "pr_seasonal_average_Climatology_PCIC-Blend_Observations_v1_1981-2010.nc",
        run=objects["run1"],
    )
    df_pcic_blend_tasmin_mon = make_data_file(
        filename=storage_root_pcic_blend_mon
        + "tasmin_monthly_average_Climatology_PCIC-Blend_Observations_v1_1981-2010.nc",
        run=objects["run1"],
    )
    df_pcic_blend_tasmax_mon = make_data_file(
        filename=storage_root_pcic_blend_mon
        + "tasmax_monthly_average_Climatology_PCIC-Blend_Observations_v1_1981-2010.nc",
        run=objects["run1"],
    )

    df_canesm2_tasmin_2050_seasonal = make_data_file(
        filename=canesm2_tasmin_root
        + "tasmin_sClim_BCCAQv2_CanESM2_historical+rcp85_r1i1p1_20400101-20691231_Canada.nc",
        run=objects["run2"],
    )
    df_canesm2_tasmax_2050_seasonal = make_data_file(
        filename=canesm2_tasmax_root
        + "tasmax_sClim_BCCAQv2_CanESM2_historical+rcp85_r1i1p1_20400101-20691231_Canada.nc",
        run=objects["run2"],
    )
    df_canesm2_tasmin_2080_seasonal = make_data_file(
        filename=canesm2_tasmin_root
        + "tasmin_sClim_BCCAQv2_CanESM2_historical+rcp85_r1i1p1_20700101-20991231_Canada.nc",
        run=objects["run2"],
    )
    df_canesm2_tasmax_2080_seasonal = make_data_file(
        filename=canesm2_tasmax_root
        + "tasmax_sClim_BCCAQv2_CanESM2_historical+rcp85_r1i1p1_20700101-20991231_Canada.nc",
        run=objects["run2"],
    )
    data_files = [v for k, v in locals().items() if k.startswith("df")]

    # Add all the above

    sesh.add_all(objects["ensembles"])
    sesh.add_all(models)
    sesh.add_all(data_files)
    sesh.add_all(objects["variable_aliases_blend"])
    sesh.add_all(objects["variable_aliases_canesm2"])
    sesh.add_all(objects["grids"])
    sesh.flush()

    # DataFileVariables

    tmin_pcic_blend_seasonal = make_data_file_variable(
        df_pcic_blend_tasmin_seasonal,
        cell_methods="time: minimum within days time: mean within seasons time: mean over years",
        variable_aliases=objects["variable_aliases_blend"],
        var_name="tasmin",
        grid=grid_pcic_blend,
    )
    tmax_pcic_blend_seasonal = make_data_file_variable(
        df_pcic_blend_tasmax_seasonal,
        cell_methods="time: maximum within days time: mean within seasons time: mean over years",
        variable_aliases=objects["variable_aliases_blend"],
        var_name="tasmax",
        grid=grid_pcic_blend,
    )
    tmin_pcic_blend_mon = make_data_file_variable(
        df_pcic_blend_tasmin_mon,
        cell_methods="time: minimum within days time: mean within months time: mean over years",
        variable_aliases=objects["variable_aliases_blend"],
        var_name="tasmin",
        grid=grid_pcic_blend,
    )
    tmax_pcic_blend_mon = make_data_file_variable(
        df_pcic_blend_tasmax_mon,
        cell_methods="time: maximum within days time: mean within months time: mean over years",
        variable_aliases=objects["variable_aliases_blend"],
        var_name="tasmax",
        grid=grid_pcic_blend,
    )

    pr_pcic_blend = make_data_file_variable(
        df_pcic_blend_pr_seasonal,
        cell_methods="time: mean time: mean over days",
        variable_aliases=objects["variable_aliases_blend"],
        var_name="pr",
        grid=grid_pcic_blend,
    )
    tmin_canesm2_2050 = make_data_file_variable(
        df_canesm2_tasmin_2050_seasonal,
        cell_methods="time: minimum",
        variable_aliases=objects["variable_aliases_canesm2"],
        var_name="tasmin",
        grid=grid_pcic_blend,
    )
    tmax_canesm2_2050 = make_data_file_variable(
        df_canesm2_tasmax_2050_seasonal,
        cell_methods="time: maximum",
        variable_aliases=objects["variable_aliases_canesm2"],
        var_name="tasmax",
        grid=grid_pcic_blend,
    )
    tmin_canesm2_2080 = make_data_file_variable(
        df_canesm2_tasmin_2080_seasonal,
        cell_methods="time: minimum",
        variable_aliases=objects["variable_aliases_canesm2"],
        var_name="tasmin",
        grid=grid_pcic_blend,
    )
    tmax_canesm2_2080 = make_data_file_variable(
        df_canesm2_tasmax_2080_seasonal,
        cell_methods="time: maximum",
        variable_aliases=objects["variable_aliases_canesm2"],
        var_name="tasmax",
        grid=grid_pcic_blend,
    )

    data_file_variables = [
        v for v in locals().values() if isinstance(v, DataFileVariableGridded)
    ]

    sesh.add_all(data_file_variables)
    sesh.flush()

    # Associate to Ensembles

    for dfv in data_file_variables:
        p2a_rules.data_file_variables.append(dfv)
    sesh.add_all(sesh.dirty)

    # TimeSets

    ts_hist_seasonal = TimeSet(
        calendar="standard",
        start_date=datetime(1981, 1, 1),
        end_date=datetime(2010, 12, 31),
        multi_year_mean=True,
        num_times=4,
        time_resolution="seasonal",
        times=[
            Time(time_idx=i, timestep=datetime(1996, 3 * i + 1, 16)) for i in range(4)
        ],
        climatological_times=[
            ClimatologicalTime(
                time_idx=i,
                time_start=datetime(1981, 3 * i + 1, 1) - relativedelta(months=1),
                time_end=datetime(2010, 3 * i + 1, 1) + relativedelta(months=2),
            )
            for i in range(4)
        ],
    )
    ts_hist_mon = TimeSet(
        calendar="standard",
        start_date=datetime(1981, 1, 1),
        end_date=datetime(2010, 12, 31),
        multi_year_mean=True,
        num_times=12,
        time_resolution="monthly",
        times=[Time(time_idx=i, timestep=datetime(1996, i + 1, 15)) for i in range(12)],
        climatological_times=[
            ClimatologicalTime(
                time_idx=i,
                time_start=datetime(1981, i + 1, 1),
                time_end=datetime(2010, i + 1, 1) + relativedelta(months=1),
            )
            for i in range(12)
        ],
    )
    ts_2050_seasonal = TimeSet(
        calendar="standard",
        start_date=datetime(2040, 1, 1),
        end_date=datetime(2069, 12, 31),
        multi_year_mean=True,
        num_times=4,
        time_resolution="seasonal",
        times=[
            Time(
                time_idx=i,
                timestep=datetime(2054, 11, 27) + relativedelta(months=3 * i),
            )
            for i in range(4)
        ],
        climatological_times=[
            ClimatologicalTime(
                time_idx=i,
                time_start=datetime(2040, 3 * i + 1, 16) - relativedelta(months=1),
                time_end=datetime(2069, 3 * i + 1, 6),
            )
            for i in range(4)
        ],
    )
    ts_2080_seasonal = TimeSet(
        calendar="standard",
        start_date=datetime(2070, 1, 1),
        end_date=datetime(2099, 12, 31),
        multi_year_mean=True,
        num_times=4,
        time_resolution="seasonal",
        times=[
            Time(
                time_idx=i,
                timestep=datetime(2084, 11, 19) + relativedelta(months=3 * i),
            )
            for i in range(4)
        ],
        climatological_times=[
            ClimatologicalTime(
                time_idx=i,
                time_start=datetime(2070, 3 * i + 1, 8) - relativedelta(months=3),
                time_end=datetime(2099, 3 * i + 1, 1),
            )
            for i in range(4)
        ],
    )
    ts_hist_seasonal.files = [
        df_pcic_blend_tasmin_seasonal,
        df_pcic_blend_tasmax_seasonal,
        df_pcic_blend_pr_seasonal,
    ]
    ts_hist_mon.files = [df_pcic_blend_tasmin_mon, df_pcic_blend_tasmax_mon]
    ts_2050_seasonal.files = [
        df_canesm2_tasmin_2050_seasonal,
        df_canesm2_tasmax_2050_seasonal,
    ]
    ts_2080_seasonal.files = [
        df_canesm2_tasmin_2080_seasonal,
        df_canesm2_tasmax_2080_seasonal,
    ]
    sesh.add_all(sesh.dirty)

    sesh.commit()
    return populateable_db


@pytest.fixture()
def populateddb_local(
    cleandb,
):
    """Create mock database only containing data files in this repository."""

    populateable_db = cleandb
    sesh = populateable_db
    objects = create_modelmeta_objects()
    p2a_rules = objects["ensembles"][0]
    grid_pcic_blend = objects["grids"][0]

    models = [objects["pcic_blend"]]

    # Data files
    df_pcic_blend_tasmin_seasonal = make_data_file(
        filename="tasmin_seasonal_average_Climatology_PCIC-Blend_Observations_v1_1981-2010.nc",
        run=objects["run1"],
    )
    df_pcic_blend_tasmax_seasonal = make_data_file(
        filename="tasmax_seasonal_average_Climatology_PCIC-Blend_Observations_v1_1981-2010.nc",
        run=objects["run1"],
    )

    data_files = [v for k, v in locals().items() if k.startswith("df")]

    # Add all the above

    sesh.add_all(objects["ensembles"])
    sesh.add_all(models)
    sesh.add_all(data_files)
    sesh.add_all(objects["variable_aliases_blend"])
    sesh.add_all(objects["grids"])
    sesh.flush()

    # DataFileVariables

    tmin_pcic_blend_seasonal = make_data_file_variable(
        df_pcic_blend_tasmin_seasonal,
        cell_methods="time: minimum time: mean over days",
        variable_aliases=objects["variable_aliases_blend"],
        var_name="tasmin",
        grid=grid_pcic_blend,
    )
    tmax_pcic_blend_seasonal = make_data_file_variable(
        df_pcic_blend_tasmax_seasonal,
        cell_methods="time: maximum time: mean over days",
        variable_aliases=objects["variable_aliases_blend"],
        var_name="tasmax",
        grid=grid_pcic_blend,
    )
    var_names = ("tmin", "tmax")
    data_file_variables = [v for k, v in locals().items() if k.startswith(var_names)]

    sesh.add_all(data_file_variables)
    sesh.flush()

    # Associate to Ensembles

    for dfv in data_file_variables:
        p2a_rules.data_file_variables.append(dfv)
    sesh.add_all(sesh.dirty)

    # TimeSets

    ts_hist_seasonal = TimeSet(
        calendar="standard",
        start_date=datetime(1981, 1, 1),
        end_date=datetime(2010, 12, 31),
        multi_year_mean=True,
        num_times=4,
        time_resolution="seasonal",
        times=[
            Time(time_idx=i, timestep=datetime(1986, 3 * i + 1, 16)) for i in range(4)
        ],
        climatological_times=[
            ClimatologicalTime(
                time_idx=i,
                time_start=datetime(1981, 3 * i + 1, 1) - relativedelta(months=1),
                time_end=datetime(2010, 3 * i + 1, 1) + relativedelta(months=2),
            )
            for i in range(4)
        ],
    )
    ts_hist_seasonal.files = [
        df_pcic_blend_tasmin_seasonal,
        df_pcic_blend_tasmax_seasonal,
    ]
    sesh.add_all(sesh.dirty)

    sesh.commit()
    return populateable_db


@pytest.fixture()
def mock_urls(requests_mock):
    requests_mock.register_uri(
        "GET",
        "https://beehive.pacificclimate.org/plan2adapt/bc_regions/ows",
        content=geoserver_data,
    )
    requests_mock.register_uri(
        "GET",
        "http://marble-dev01.pcic.uvic.ca/twitcher/ows/proxy/thredds/fileServer/datasets"
        "/storage/data/climate/downscale/MBCn/PCIC-Blend/Derived/seasonal/climatologies/"
        "tasmin_seasonal_average_Climatology_PCIC-Blend_Observations_v1_1981-2010.nc",
        content=tasmin_data,
    )
    requests_mock.register_uri(
        "GET",
        "http://marble-dev01.pcic.uvic.ca/twitcher/ows/proxy/thredds/fileServer/datasets"
        "/storage/data/climate/downscale/MBCn/PCIC-Blend/Derived/seasonal/climatologies/"
        "tasmax_seasonal_average_Climatology_PCIC-Blend_Observations_v1_1981-2010.nc",
        content=tasmax_data,
    )
