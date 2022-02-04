import pytest
import py.path
import tempfile
from ce import get_app
from datetime import datetime
from pkg_resources import resource_filename
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
from mm_cataloguer import index_netcdf
from flask_sqlalchemy import SQLAlchemy
from netCDF4 import Dataset


@pytest.fixture
def mock_thredds_url_root(monkeypatch):
    monkeypatch.setenv(
        "THREDDS_URL_ROOT",
        "https://docker-dev03.pcic.uvic.ca/twitcher/ows/proxy/thredds/dodsC/datasets",
    )


@pytest.fixture(scope="function")
def ce_response():
    return {
        "test_period_20100101-20391230": {"mean": 1, "min": 0, "max": 2},
        "test_period_20400101-20691231": {"mean": 3, "min": 1, "max": 5},
        "test_period_20700101-20991231": {"mean": 5, "min": 0, "max": 10},
    }


@pytest.fixture(scope="function")
def sessiondir(request,):
    dir = py.path.local(tempfile.mkdtemp())
    request.addfinalizer(lambda: dir.remove(rec=1))
    return dir


@pytest.fixture(scope="function")
def dsn(sessiondir,):
    return "sqlite:///{}".format(sessiondir.join("test.sqlite").realpath())


@pytest.fixture
def app(dsn,):
    app = get_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = dsn
    app.config["SQLALCHEMY_ECHO"] = False
    return app


@pytest.fixture
def cleandb(app,):
    db = SQLAlchemy(app)
    metadata.create_all(bind=db.engine)
    db.create_all()
    return db


@pytest.fixture
def populateddb(cleandb,):

    now = datetime.utcnow()

    populateable_db = cleandb
    sesh = populateable_db.session

    # Ensembles

    p2a_rules = Ensemble(name="p2a_rules", version=1.0, changes="", description="",)
    ensembles = [
        p2a_rules,
    ]

    # Emissions
    historical = Emission(short_name="historical")

    # Runs
    run = Run(name="r1i1p1", emission=historical,)

    # Models

    bnu = Model(short_name="BNU-ESM", type="GCM", runs=[run], organization="BNU")
    anusplin = Model(short_name="anusplin", type="GCM", runs=[run], organization="")
    models = [bnu, anusplin]

    # Data files

    def make_data_file(
        unique_id, filename=None, run=None,
    ):
        if not filename:
            filename = "{}.nc".format(unique_id)
        if not filename.startswith("/"):
            filename = resource_filename("ce", "tests/data/{}".format(filename),)
        return DataFile(
            filename=filename,
            unique_id=unique_id,
            first_1mib_md5sum="xxxx",
            x_dim_name="lon",
            y_dim_name="lat",
            index_time=now,
            run=run,
        )

    df_bnu_seasonal = make_data_file(
        unique_id="tasmin_sClim_BNU-ESM_historical_r1i1p1_19650101-19701230", run=run,
    )
    df_anusplin_tasmin_seasonal = make_data_file(
        unique_id="tasmin_sClimMean_anusplin_historical_19710101-20001231",
        filename="/storage/data/climate/downscale/BCCAQ2/ANUSPLIN/climatologies/tasmin_sClimMean_anusplin_historical_19710101-20001231.nc",
        run=run,
    )
    df_anusplin_tasmax_seasonal = make_data_file(
        unique_id="tasmax_sClimMean_anusplin_historical_19710101-20001231",
        filename="/storage/data/climate/downscale/BCCAQ2/ANUSPLIN/climatologies/tasmax_sClimMean_anusplin_historical_19710101-20001231.nc",
        run=run,
    )
    data_files = [
        df_bnu_seasonal,
        df_anusplin_tasmin_seasonal,
        df_anusplin_tasmax_seasonal,
    ]

    # VariableAlias

    tasmin = VariableAlias(
        long_name="Daily Minimum Temperature",
        standard_name="air_temperature",
        units="degC",
    )
    tasmax = VariableAlias(
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
        long_name="Flow Direction", standard_name="flow_direction", units="1",
    )
    variable_aliases = [
        tasmin,
        tasmax,
        pr,
        flow_direction,
    ]

    # Grids

    grid_anuspline = Grid(
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
    grids = [grid_anuspline]

    # Add all the above

    sesh.add_all(ensembles)
    sesh.add_all(models)
    sesh.add_all(data_files)
    sesh.add_all(variable_aliases)
    sesh.add_all(grids)
    sesh.flush()

    # DataFileVariable

    def make_data_file_variable(
        file, cell_methods, var_name=None, grid=grid_anuspline,
    ):
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

    tmax_bnu = make_data_file_variable(
        df_bnu_seasonal, cell_methods="time: maximum", var_name="tasmin",
    )
    tmin_anusplin = make_data_file_variable(
        df_anusplin_tasmin_seasonal,
        cell_methods="time: minimum time: mean over days",
        var_name="tasmin",
    )
    tmax_anusplin = make_data_file_variable(
        df_anusplin_tasmax_seasonal,
        cell_methods="time: maximum time: mean over days",
        var_name="tasmax",
    )
    data_file_variables = [tmax_bnu, tmin_anusplin, tmax_anusplin]

    sesh.add_all(data_file_variables)
    sesh.flush()

    # Associate to Ensembles

    for dfv in data_file_variables:
        p2a_rules.data_file_variables.append(dfv)
    sesh.add_all(sesh.dirty)

    # TimeSets

    ts_seasonal = TimeSet(
        calendar="standard",
        start_date=datetime(1971, 1, 1,),
        end_date=datetime(2000, 12, 31,),
        multi_year_mean=True,
        num_times=4,
        time_resolution="seasonal",
        times=[
            Time(time_idx=i, timestep=datetime(1986, 3 * i + 1, 16,),) for i in range(4)
        ],
        climatological_times=[
            ClimatologicalTime(
                time_idx=i,
                time_start=datetime(1971, 3 * i + 1, 1,) - relativedelta(months=1),
                time_end=datetime(2000, 3 * i + 1, 1,) + relativedelta(months=2),
            )
            for i in range(4)
        ],
    )
    ts_seasonal.files = [
        df_bnu_seasonal,
        df_anusplin_tasmin_seasonal,
        df_anusplin_tasmax_seasonal,
    ]
    sesh.add_all(sesh.dirty)

    sesh.commit()
    return populateable_db
