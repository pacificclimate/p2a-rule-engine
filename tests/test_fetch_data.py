import pytest

from p2a_impacts.fetch_data import (
    read_csv,
    filter_by_period,
    translate_args,
    get_nffd,
    calculate_result,
)


@pytest.mark.parametrize(
    ("expected_rules", "expected_conds"),
    [
        (
            [
                "rule_snow",
                "rule_hybrid",
                "rule_rain",
                "rule_future-snow",
                "rule_future-hybrid",
                "rule_future-rain",
                "rule_shm",
            ],
            [
                "(temp_djf_iamean_s0p_hist <= -6)",
                "((temp_djf_iamean_s0p_hist <= -6)"
                " && (temp_djf_iamean_s100p_hist >= -6))"
                " || ((temp_djf_iamean_s0p_hist <= 5) && "
                "(temp_djf_iamean_s100p_hist >= 5)) || ((temp_djf_iamean_s0p_hist >= -6)"
                " && (temp_djf_iamean_s100p_hist <= 5))",
                "(temp_djf_iamean_s100p_hist >= 5)",
                "(temp_djf_iamean_s0p_hist + " "temp_djf_iamean_s0p_e25p <= -6)",
                "((temp_djf_iamean_s0p_hist + "
                "temp_djf_iamean_s0p_e25p <= -6) && (temp_djf_iamean_s100p_hist + "
                "temp_djf_iamean_s100p_e75p >= -6)) || ((temp_djf_iamean_s0p_hist + "
                "temp_djf_iamean_s0p_e25p <= 5) && (temp_djf_iamean_s100p_hist + "
                "temp_djf_iamean_s100p_e75p >= 5)) || ((temp_djf_iamean_s0p_hist + "
                "temp_djf_iamean_s0p_e75p >= -6) && (temp_djf_iamean_s100p_hist + "
                "temp_djf_iamean_s100p_e25p <= 5))",
                "(temp_djf_iamean_s100p_hist + " "temp_djf_iamean_s100p_e75p >= 5)",
                "(temp_jul_iamean_smean_hist / ((prec_jja_iamean_smean_hist / 1000) * 92))",
            ],
        )
    ],
)
def test_read_csv(expected_rules, expected_conds):
    rules = read_csv("tests/rules-test.csv")
    for rule, cond in rules.items():
        assert rule in expected_rules
        assert cond in expected_conds


@pytest.mark.parametrize(
    ("target", "dates", "expected"),
    [
        ("mean", ["20100101-20391231", "20110101-20400101", "20100101-20391230"], 1),
        ("min", ["20400101-20691231"], 1),
        ("max", ["20700101-20991231"], 10),
    ],
)
def test_filter_by_period(target, dates, ce_response, expected):
    assert expected == filter_by_period(target, dates, ce_response)


@pytest.mark.parametrize(
    ("target", "dates"),
    [
        ("bad_target", ["20100101-20391231", "20110101-20400101", "20100101-20391230"]),
        ("min", ["bad_dates"]),
    ],
)
def test_filter_by_period_bad_vars(target, dates, ce_response):
    assert filter_by_period(target, dates, ce_response) is None


@pytest.mark.parametrize(
    (
        "variable",
        "time_of_year",
        "cell_method",
        "spatial",
        "percentile",
        "area",
        "date_range",
        "ensemble",
        "thredds",
        "expected",
    ),
    [
        (
            "temp",
            "djf",
            "iamean",
            "smean",
            "e25p",
            {
                "the_geom": """POLYGON((-122.70904541015625 49.31438004800689,
            -122.92327880859375 49.35733376286064,-123.14849853515625
            49.410973199695846,-123.34625244140625
            49.30721745093609,-123.36273193359375
            49.18170338770662,-123.20343017578125
            49.005447494058096,-122.44537353515625
            49.023461463214126,-122.46734619140625
            49.13500260581219,-122.50579833984375
            49.31079887964633,-122.70904541015625 49.31438004800689))"""
            },
            "2020",
            "p2a_files",
            True,
            {
                "variable": ["tasmin", "tasmax"],
                "cell_method": "mean",
                "spatial": "mean",
                "percentile": 25,
                "emission": "historical,rcp85",
                "time": 0,
                "timescale": "seasonal",
                "area": """POLYGON((-122.70904541015625 49.31438004800689,
            -122.92327880859375 49.35733376286064,-123.14849853515625
            49.410973199695846,-123.34625244140625
            49.30721745093609,-123.36273193359375
            49.18170338770662,-123.20343017578125
            49.005447494058096,-122.44537353515625
            49.023461463214126,-122.46734619140625
            49.13500260581219,-122.50579833984375
            49.31079887964633,-122.70904541015625 49.31438004800689))""",
                "dates": [
                    "20100101-20391231",
                    "20110101-20400101",
                    "20100101-20391230",
                ],
                "ensemble_name": "p2a_files",
                "thredds": True,
            },
        )
    ],
)
def test_translate_args(
    variable,
    time_of_year,
    cell_method,
    spatial,
    percentile,
    area,
    date_range,
    ensemble,
    thredds,
    expected,
):  # noqa
    test_args = translate_args(
        variable,
        time_of_year,
        cell_method,
        spatial,
        percentile,
        area,
        date_range,
        ensemble,
        thredds,
    )
    for key in test_args.keys():
        assert test_args[key] == expected[key]


@pytest.mark.parametrize(
    ("fd", "time", "timescale", "expected"),
    [
        (50, 0, "seasonal", 39),
        (60, 1, "seasonal", 32),
        (70, 2, "seasonal", 22),
        (80, 3, "seasonal", 11),
        (150, 0, "yearly", 215),
    ],
)
def test_get_nffd(fd, time, timescale, expected):
    assert get_nffd(fd, time, timescale) == expected


@pytest.mark.parametrize(
    ("fd", "time", "timescale", "calendar"), [(50, 0, "seasonal", "not implemented"),],
)
def test_get_nffd_bad_calendar(fd, time, timescale, calendar):
    with pytest.raises(NotImplementedError) as e:
        get_nffd(fd, time, timescale, calendar)


@pytest.mark.parametrize(
    ("vals_to_calc", "variables", "time", "timescale", "expected"),
    [
        ([0, 10], ["tasmin", "tasmax"], 0, "seasonal", 5),
        ([80], ["fdETCCDI"], 3, "seasonal", 11),
        ([150], ["fdETCCDI"], 0, "yearly", 215),
        ([10], [], 0, "yearly", 10),
    ],
)
def test_calculate_result(vals_to_calc, variables, time, timescale, expected):
    assert calculate_result(vals_to_calc, variables, time, timescale) == expected


@pytest.mark.parametrize(
    ("vals_to_calc", "variables", "time", "timescale"),
    [
        (["bad", "type"], ["tasmin", "tasmax"], 0, "seasonal"),
        (["bad_type"], ["fdETCCDI"], 3, "seasonal"),
    ],
)
def test_calculate_result_bad_type(vals_to_calc, variables, time, timescale):
    with pytest.raises(TypeError) as e:
        calculate_result(vals_to_calc, variables, time, timescale)
