"""
The purpose of this script is to collect all the /storage/ filepaths used by
the p2a_impacts package.
"""

from argparse import ArgumentParser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

from ce.api.util import search_for_unique_ids
from modelmeta import DataFile
from p2a_impacts.parser import build_parse_tree
from p2a_impacts.evaluator import evaluate_rule
from p2a_impacts.fetch_data import (
    get_dict_val,
    read_csv,
    translate_args,
    get_models,
)
from p2a_impacts.utils import get_region, REGIONS


def setup_logging(log_level):
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger("scripts")
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, log_level))
    return logger


logger = setup_logging("INFO")


def file_collection(csv, date_range, region, ensemble, connection_string):
    """
    Builds the variables that would be used in in p2a_impacts.resolve_rules
    to the point of accessing the climate explorer database, but instead of evaluating
    a rule it writes the paths for the files used to a text file.
    """

    # read csv
    logger.info("Reading {}".format(csv))
    rules = read_csv(csv)

    # create parse tree dictionary and gather unique variables
    logger.info("Building parse tree")
    parse_trees = {}
    variables = {}
    region_variable = None
    for rule, condition in rules.items():
        try:
            parse_trees[rule], vars, region_var = build_parse_tree(condition)
        except SyntaxError as e:
            logger.warning("{}, rule will be excluded".format(e))
            continue

        # check region var
        if region_var:
            region_variable = region_var

        # add unique variables to set
        for name, values in vars.items():
            if name not in variables.keys():
                variables[name] = values

    # get values for all variables we would need if we were doing an evaluation
    logger.info("Collecting variables")
    Session = sessionmaker(create_engine(connection_string))
    sesh = Session()

    # write file paths for each variable to text file
    for name, values in variables.items():
        write_file_paths(sesh, values, ensemble, date_range, region)


def write_file_paths(sesh, variables, ensemble, date_range, area):
    """Given a variable name write the required file's path to file_paths.txt
    by querying the CE backend.
    """
    logger.info("")
    logger.info("Translating variables for query")
    query_args = translate_args(
        variables["variable"],
        variables["time_of_year"],
        variables["temporal"],
        variables["spatial"],
        variables["percentile"],
        area,
        date_range,
        ensemble,
    )

    logger.info("Collecting models")
    models = get_models(sesh, variables["percentile"], ensemble)

    var_name = "_".join(
        [
            variables["variable"],
            variables["time_of_year"],
            variables["temporal"],
            variables["spatial"],
            variables["percentile"],
        ]
    )

    logger.info("Fetching data for {}".format(var_name))

    paths = []
    [paths.extend(query_backend(sesh, model, query_args)) for model in models]
    logger.info("Writing file path for {} to file".format(var_name))

    with open("file_paths.txt", "a") as file_:
        for path in paths:
            file_.write(path + "\n")


def query_backend(sesh, model, query_args):
    """Return the desired file name for a particular climate model"""
    logger.debug("Running query_backend() with args: %s, %s", model, query_args)
    ids = [
        search_for_unique_ids(
            sesh,
            ensemble_name=query_args["ensemble_name"],
            model=model,
            emission=query_args["emission"],
            time=query_args["time"],
            variable=var,
            timescale=query_args["timescale"],
            cell_method=query_args["cell_method"],
        )
        for var in query_args["variable"]
    ]
    file_names = []
    for id_ in ids:
        for model_id in list(id_):
            data_file = (
                sesh.query(DataFile).filter(DataFile.unique_id == model_id).one()
            )
            if data_file is not None:
                file_names.append(data_file.filename)
    return file_names


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-c", "--csv", help="CSV file containing rules", default="./data/rules.csv",
    )
    parser.add_argument(
        "-d",
        "--date-range",
        help="30 year period for data",
        choices=["2020", "2050", "2080"],
        default="2080",
    )
    parser.add_argument(
        "-r", "--region", help="Selected region", default="bc", choices=REGIONS.keys()
    )
    parser.add_argument(
        "-u",
        "--url",
        help="Geoserver URL",
        default="http://docker-dev01.pcic.uvic.ca:30123/geoserver/bc_regions/ows",
    )
    parser.add_argument(
        "-x",
        "--connection-string",
        help="Database connection string",
        default="postgres://ce_meta_ro@db3.pcic.uvic.ca/ce_meta_12f290b63791",
    )
    parser.add_argument(
        "-e",
        "--ensemble",
        help="Ensemble name filter for data files",
        default="p2a_rules",
    )
    args = parser.parse_args()
    region = get_region(args.region, args.url)

    file_collection(
        args.csv, args.date_range, region, args.ensemble, args.connection_string
    )
