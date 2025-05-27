from importlib.resources import files

geoserver_data = open(files("tests") / f"data/geoserver_van.txt", "rb").read()


def get_nc_data(filename):
    f = open(files("tests") / f"data/{filename}", "rb")
    filedata = f.read()
    f.close()
    return filedata


tasmin_filename = (
    "tasmin_seasonal_average_Climatology_PCIC-Blend_Observations_v1_1981-2010.nc"
)
tasmax_filename = (
    "tasmax_seasonal_average_Climatology_PCIC-Blend_Observations_v1_1981-2010.nc"
)
tasmin_data = get_nc_data(tasmin_filename)
tasmax_data = get_nc_data(tasmax_filename)
