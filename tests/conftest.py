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
from flask_sqlalchemy import SQLAlchemy


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

    p2a_rules = Ensemble(name="p2a_rules", version=1.0, changes="", description="")
    ensembles = [
        p2a_rules,
    ]

    # Emissions
    historical = Emission(short_name="historical")
    historical_rcp85 = Emission(short_name="historical,rcp85")

    # Runs
    run1 = Run(name="r1i1p1", emission=historical)
    run2 = Run(name="r1i1p1", emission=historical_rcp85)

    # Models

    bnu = Model(short_name="BNU-ESM", type="GCM", runs=[run1], organization="BNU")
    anusplin = Model(short_name="anusplin", type="GCM", runs=[run1], organization="")
    canesm2 = Model(short_name="CanESM2", type="GCM", runs=[run2], organization="")
    models = [bnu, anusplin, canesm2]

    # Data files

    def make_data_file(
        unique_id, filename=None, run=None,
    ):
        if not filename:
            filename = "{}.nc".format(unique_id)
        if not filename.startswith("/"):
            filename = resource_filename("ce", "tests/data/{}".format(filename))
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
        unique_id="tasmin_sClim_BNU-ESM_historical_r1i1p1_19650101-19701230", run=run1,
    )
    df_anusplin_tasmin_seasonal = make_data_file(
        unique_id="tasmin_sClimMean_anusplin_historical_19710101-20001231",
        filename="/storage/data/climate/downscale/BCCAQ2/ANUSPLIN/climatologies/tasmin_sClimMean_anusplin_historical_19710101-20001231.nc",
        run=run1,
    )
    df_anusplin_tasmax_seasonal = make_data_file(
        unique_id="tasmax_sClimMean_anusplin_historical_19710101-20001231",
        filename="/storage/data/climate/downscale/BCCAQ2/ANUSPLIN/climatologies/tasmax_sClimMean_anusplin_historical_19710101-20001231.nc",
        run=run1,
    )
    df_anusplin_tasmin_mon = make_data_file(
        unique_id="tasmin_mClimMean_anusplin_historical_19710101-20001231",
        filename="/storage/data/climate/downscale/BCCAQ2/ANUSPLIN/climatologies/tasmin_mClimMean_anusplin_historical_19710101-20001231.nc",
        run=run1,
    )
    df_anusplin_tasmax_mon = make_data_file(
        unique_id="tasmax_mClimMean_anusplin_historical_19710101-20001231",
        filename="/storage/data/climate/downscale/BCCAQ2/ANUSPLIN/climatologies/tasmax_mClimMean_anusplin_historical_19710101-20001231.nc",
        run=run1,
    )
    df_anusplin_pr_seasonal = make_data_file(
        unique_id="pr_sClimMean_anusplin_historical_19710101-20001231",
        filename="/storage/data/climate/downscale/BCCAQ2/ANUSPLIN/climatologies/pr_sClimMean_anusplin_historical_19710101-20001231.nc",
        run=run1,
    )
    df_canesm2_tasmin_2050_seasonal = make_data_file(
        unique_id="tasmin_sClim_BCCAQv2_CanESM2_historical+rcp85_r1i1p1_20400101-20691231_Canada",
        filename="/storage/data/projects/comp_support/climate_explorer_data_prep/climatological_means/downscale/output/2433/tasmin_sClim_BCCAQv2_CanESM2_historical+rcp85_r1i1p1_20400101-20691231_Canada.nc",
        run=run2,
    )
    df_canesm2_tasmax_2050_seasonal = make_data_file(
        unique_id="tasmax_sClim_BCCAQv2_CanESM2_historical+rcp85_r1i1p1_20400101-20691231_Canada",
        filename="/storage/data/projects/comp_support/climate_explorer_data_prep/climatological_means/downscale/output/2495/tasmax_sClim_BCCAQv2_CanESM2_historical+rcp85_r1i1p1_20400101-20691231_Canada.nc",
        run=run2,
    )
    df_canesm2_tasmin_2080_seasonal = make_data_file(
        unique_id="tasmin_sClim_BCCAQv2_CanESM2_historical+rcp85_r1i1p1_20700101-20991231_Canada",
        filename="/storage/data/projects/comp_support/climate_explorer_data_prep/climatological_means/downscale/output/2433/tasmin_sClim_BCCAQv2_CanESM2_historical+rcp85_r1i1p1_20700101-20991231_Canada.nc",
        run=run2,
    )
    df_canesm2_tasmax_2080_seasonal = make_data_file(
        unique_id="tasmax_sClim_BCCAQv2_CanESM2_historical+rcp85_r1i1p1_20700101-20991231_Canada",
        filename="/storage/data/projects/comp_support/climate_explorer_data_prep/climatological_means/downscale/output/2495/tasmax_sClim_BCCAQv2_CanESM2_historical+rcp85_r1i1p1_20700101-20991231_Canada.nc",
        run=run2,
    )
    data_files = [
        df_bnu_seasonal,
        df_anusplin_tasmin_seasonal,
        df_anusplin_tasmax_seasonal,
        df_anusplin_tasmin_mon,
        df_anusplin_tasmax_mon,
        df_anusplin_pr_seasonal,
        df_canesm2_tasmin_2050_seasonal,
        df_canesm2_tasmax_2050_seasonal,
        df_canesm2_tasmin_2080_seasonal,
        df_canesm2_tasmax_2080_seasonal,
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
    tmin_anusplin_seasonal = make_data_file_variable(
        df_anusplin_tasmin_seasonal,
        cell_methods="time: minimum time: mean over days",
        var_name="tasmin",
    )
    tmax_anusplin_seasonal = make_data_file_variable(
        df_anusplin_tasmax_seasonal,
        cell_methods="time: maximum time: mean over days",
        var_name="tasmax",
    )
    tmin_anusplin_mon = make_data_file_variable(
        df_anusplin_tasmin_mon,
        cell_methods="time: minimum time: mean over days",
        var_name="tasmin",
    )
    tmax_anusplin_mon = make_data_file_variable(
        df_anusplin_tasmax_mon,
        cell_methods="time: minimum time: mean over days",
        var_name="tasmax",
    )
    pr_anusplin = make_data_file_variable(
        df_anusplin_pr_seasonal,
        cell_methods="time: mean time: mean over days",
        var_name="pr",
    )
    tmin_canesm2_2050 = make_data_file_variable(
        df_canesm2_tasmin_2050_seasonal,
        cell_methods="time: minimum",
        var_name="tasmin",
    )
    tmax_canesm2_2050 = make_data_file_variable(
        df_canesm2_tasmax_2050_seasonal,
        cell_methods="time: maximum",
        var_name="tasmax",
    )
    tmin_canesm2_2080 = make_data_file_variable(
        df_canesm2_tasmin_2080_seasonal,
        cell_methods="time: minimum",
        var_name="tasmin",
    )
    tmax_canesm2_2080 = make_data_file_variable(
        df_canesm2_tasmax_2080_seasonal,
        cell_methods="time: maximum",
        var_name="tasmax",
    )
    data_file_variables = [
        tmax_bnu,
        tmin_anusplin_seasonal,
        tmax_anusplin_seasonal,
        tmin_anusplin_mon,
        tmax_anusplin_mon,
        pr_anusplin,
        tmin_canesm2_2050,
        tmax_canesm2_2050,
        tmin_canesm2_2080,
        tmax_canesm2_2080,
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
        start_date=datetime(1971, 1, 1),
        end_date=datetime(2000, 12, 31),
        multi_year_mean=True,
        num_times=4,
        time_resolution="seasonal",
        times=[
            Time(time_idx=i, timestep=datetime(1986, 3 * i + 1, 16)) for i in range(4)
        ],
        climatological_times=[
            ClimatologicalTime(
                time_idx=i,
                time_start=datetime(1971, 3 * i + 1, 1) - relativedelta(months=1),
                time_end=datetime(2000, 3 * i + 1, 1) + relativedelta(months=2),
            )
            for i in range(4)
        ],
    )
    ts_hist_mon = TimeSet(
        calendar="standard",
        start_date=datetime(1971, 1, 1),
        end_date=datetime(2000, 12, 31),
        multi_year_mean=True,
        num_times=12,
        time_resolution="monthly",
        times=[Time(time_idx=i, timestep=datetime(1986, i + 1, 15)) for i in range(12)],
        climatological_times=[
            ClimatologicalTime(
                time_idx=i,
                time_start=datetime(1971, i + 1, 1),
                time_end=datetime(2000, i + 1, 1) + relativedelta(months=1),
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
            Time(time_idx=0, timestep=datetime(2054, 11, 27)),
            Time(time_idx=1, timestep=datetime(2055, 2, 25)),
            Time(time_idx=2, timestep=datetime(2055, 5, 27)),
            Time(time_idx=3, timestep=datetime(2055, 8, 27)),
        ],
        climatological_times=[
            ClimatologicalTime(
                time_idx=0,
                time_start=datetime(2039, 10, 16),
                time_end=datetime(2069, 1, 6),
            ),
            ClimatologicalTime(
                time_idx=1,
                time_start=datetime(2040, 1, 14),
                time_end=datetime(2069, 4, 8),
            ),
            ClimatologicalTime(
                time_idx=2,
                time_start=datetime(2040, 4, 15),
                time_end=datetime(2069, 7, 9),
            ),
            ClimatologicalTime(
                time_idx=3,
                time_start=datetime(2040, 7, 16),
                time_end=datetime(2069, 10, 8),
            ),
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
            Time(time_idx=0, timestep=datetime(2084, 11, 1,)),
            Time(time_idx=1, timestep=datetime(2085, 2, 17)),
            Time(time_idx=2, timestep=datetime(2085, 5, 19)),
            Time(time_idx=3, timestep=datetime(2085, 8, 19)),
        ],
        climatological_times=[
            ClimatologicalTime(
                time_idx=0,
                time_start=datetime(2069, 10, 8),
                time_end=datetime(2098, 12, 30),
            ),
            ClimatologicalTime(
                time_idx=1,
                time_start=datetime(2070, 1, 6),
                time_end=datetime(2099, 4, 1),
            ),
            ClimatologicalTime(
                time_idx=2,
                time_start=datetime(2070, 4, 8),
                time_end=datetime(2099, 7, 2),
            ),
            ClimatologicalTime(
                time_idx=3,
                time_start=datetime(2070, 7, 9),
                time_end=datetime(2099, 10, 1),
            ),
        ],
    )
    ts_hist_seasonal.files = [
        df_bnu_seasonal,
        df_anusplin_tasmin_seasonal,
        df_anusplin_tasmax_seasonal,
        df_anusplin_pr_seasonal,
    ]
    ts_hist_mon.files = [df_anusplin_tasmin_mon, df_anusplin_tasmax_mon]
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
