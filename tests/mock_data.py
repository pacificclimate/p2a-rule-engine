from pkg_resources import resource_filename
from netCDF4 import Dataset

geoserver_data = open(resource_filename("tests", "data/geoserver_van.txt"), "rb").read()


def get_nc_data(filename):
    f = open(resource_filename("tests", f"data/{filename}"), "rb")
    filedata = f.read()
    f.close()
    return filedata


tasmin_filename = "tasmin_sClimMean_anusplin_historical_19710101-20001231.nc"
tasmax_filename = "tasmax_sClimMean_anusplin_historical_19710101-20001231.nc"
tasmin_data = get_nc_data(tasmin_filename)
tasmax_data = get_nc_data(tasmax_filename)
