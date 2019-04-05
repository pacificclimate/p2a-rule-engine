# Rule Resolver
Uses [SLY](https://github.com/dabeaz/sly) to process _planners-impacts.csv_.  The output of the module is a dictionary with the truth value of each of the rules in the _planners-impacts.csv_.

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

Next ensure that you install all the requirements.
```
(venv)$ export CPLUS_INCLUDE_PATH=/usr/include/gdal
(venv)$ export C_INCLUDE_PATH=/usr/include/gdal
(venv)$ pip install -i https://pypi.pacificclimate.org/simple -r requirements.txt
```

### Run
```
(venv)$ python scripts/main.py --csv planners-impacts.csv --date '2020s' --region
```


### Program Flow
```
Read planners-impacts.csv and extract id and condition columns (main.py)
| | Input: .csv file
| | Output: dictionary {rule: condition}
|/
Process conditions using SLY into parse trees (resolver.py)
| | Input: string
| | Output: parse tree tuple
|/
Evaluate parse trees to determine truth value of each rule (evaluator.py)
| | Input: parse tree tuple
| | Output: truth value of parse tree (there are some cases where the output of the rule is actually a value)
|/
Print result dictionary {rule: True/False/Value} (main.py)
```

### Testing
Uses [pytest](https://github.com/pytest-dev/pytest).
```
pytest tests/ --cov --flake8 --cov-report term-missing
```
