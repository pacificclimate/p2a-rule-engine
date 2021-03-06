# Rule Engine
Uses [SLY](https://github.com/dabeaz/sly) to process csv file containing rules.  The output of the module is a dictionary with the truth value of each of the rules in the csv file.

Example output:
```
{
    'rule_snow': True,
    'rule_hybrid': True,
    'rule_rain': True,
    'rule_future-snow': False,
    'rule_future-hybrid': True,
    'rule_future-rain': True,
    ...
}
```

## Setup
Project setup is automated by `make`.
```
make
source /tmp/p2a-re-venv/bin/activate
```

## Manual Setup
If you do not wish to use `make`, follow the steps below to setup the project.

### Step 1: Create `venv`
To run the program create and enter a python3 (3.6+) virtual environment.
```
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install requirements
Once you have activated the `venv` you can install the required packages.
```
sudo apt-get install -y libpq-dev python3-dev libhdf5-dev libnetcdf-dev libgdal-dev
export CPLUS_INCLUDE_PATH=/usr/include/gdal
export C_INCLUDE_PATH=/usr/include/gdal
pip install -i https://pypi.pacificclimate.org/simple -r requirements.txt
pip install -e .
```

### Step 3: `.pgpass`
To connect to the database the script expects there to be a `.pgpass` file for it to read. It should look like so:
```
database:port:*:username:password
```
You can find these items in TPM.

### Step 4: Pre-commit hook
While not required, the `pre-commit` hook will help you avoid formatting errors in `actions` during development. While in `venv` run:
```
pre-commit install
```
This will check each of your commits against the `.pre-commit-config.yml` to ensure it meets the standard.

## Run
To run the rule engine and view the results use `process.py` script.
```
(venv)$ process.py --csv data/rules.csv --date-range [date-option] --region [region-option]
```

If you wish to use the `--thredds` option please set the appropriate env variable:
```
export THREDDS_URL_ROOT=https://docker-dev03.pcic.uvic.ca/twitcher/ows/proxy/thredds/dodsC/datasets
```

### Program Flow
```
Read csv and extract id and condition columns (resolver.py)
| | Input: csv file
| | Output: dictionary {rule: condition}
|/
Process conditions using SLY into parse trees (parser.py)
| | Input: string
| | Output: parse tree tuple
|/
Evaluate parse trees to determine truth value of each rule (evaluator.py)
| | Input: parse tree tuple
| | Output: truth value of parse tree (there are some cases where the output of the rule is actually a value)
|/
Return result dictionary {rule: True/False/Value} (resolver.py)
```

## Testing
Uses [pytest](https://github.com/pytest-dev/pytest).
```
pytest tests/ --cov --flake8 --cov-report term-missing
```

## Troubleshooting
### Unhashable type: 'MaskedArray' error
Solution for this [issue](https://github.com/pacificclimate/climate-explorer-backend/issues/97) is ongoing.  A temporary solution is to replace some code in the virtual environment.

Open up the file that's causing the issue.
```
$ vi venv/lib/python3.6/site-packages/ce/api/geo.py  
```

Find the definition for the `make_mask_grid_key(...)` method and replace this chunk:
```
latsteps = nc.variables['lat'].shape[0]
latmin = nc.variables['lat'][0]
latmax = nc.variables['lat'][latsteps - 1]
lonsteps = nc.variables['lon'].shape[0]
lonmin = nc.variables['lon'][0]
lonmax = nc.variables['lon'][lonsteps - 1]
```
With this:
```
latsteps = nc.variables['lat'].shape[0]
latmin = np.min(nc.variables['lat'][:])
latmax = np.max(nc.variables['lat'][:])
lonsteps = nc.variables['lon'].shape[0]
lonmin = np.min(nc.variables['lon'][:])
lonmax = np.max(nc.variables['lon'][:])
```
This should take care of the issue.

### No such file or directory error
In the case that an error in this form occurs:
```
NETCDF:"file.nc":some_variable: No such file or directory
```
Try the following:
```
(venv)$ pip uninstall rasterio
(venv)$ pip install rasterio==1.0.22 --no-binary rasterio
```
This should fix the issue as it is likely that `rasterio` and `GDAL` were not working together properly.

## Releasing

1. Increment `__version__` in `setup.py`
2. Summarize release changes in `NEWS.md`
3. Commit these changes, then tag the release
```
git add setup.py NEWS.md
git commit -m"Bump to version x.x.x"
git tag -a -m"x.x.x" x.x.x
git push --follow-tags
```
4. Our Github Actions [workflow](https://github.com/pacificclimate/p2a-rule-engine/blob/master/.github/workflows/pypi-publish.yml) will build and release the package
