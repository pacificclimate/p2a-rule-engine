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

### Setup
To run the program create and enter a python3 virtual environment.
```
$python3 -m venv venv
$source venv/bin/activate
```

Install requirements.
```
(venv)$ export CPLUS_INCLUDE_PATH=/usr/include/gdal
(venv)$ export C_INCLUDE_PATH=/usr/include/gdal
(venv)$ pip install -i https://pypi.pacificclimate.org/simple -r requirements.txt
```

### Run
To run the rule engine and view the results use `process.py`.
```
(venv)$ python scripts/process.py --csv rules.csv --date [date-option] --region [region-option]
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

### Troubleshooting
#### No such file or directory error
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

### Testing
Uses [pytest](https://github.com/pytest-dev/pytest).
```
pytest tests/ --cov --flake8 --cov-report term-missing
```
