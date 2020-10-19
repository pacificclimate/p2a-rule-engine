"""
The purpose of this script is to collect all the /storage/ filepaths used by
the p2a_impacts package.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import click

from p2a_impacts.utils import get_region, REGIONS, setup_logging
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


@click.command()
@click.option(
    "-c", "--csv", help="CSV file containing rules", default="./data/rules.csv"
)
@click.option(
    "-d",
    "--date-range",
    help="30 year period for data",
    default=["2020", "2050", "2080"],
    type=click.Choice(["2020", "2050", "2080"]),
    multiple=True,
)
@click.option(
    "-r",
    "--region",
    help="Selected region",
    default="bc",
    type=click.Choice(REGIONS.keys()),
)
@click.option(
    "-u",
    "--url",
    help="Geoserver URL",
    default="http://docker-dev01.pcic.uvic.ca:30123/geoserver/bc_regions/ows",
)
@click.option(
    "-x",
    "--connection-string",
    help="Database connection string",
    default="postgres://ce_meta_ro@db3.pcic.uvic.ca/ce_meta_12f290b63791",
)
@click.option(
    "-e", "--ensemble", help="Ensemble name filter for data files", default="p2a_rules"
)
@click.option("-f", "--output_file", help="Path to output file", default="output.txt")
@click.option(
    "-l",
    "--log_level",
    help="Logging level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
)
def file_collection(
    csv, date_range, region, url, ensemble, connection_string, output_file, log_level
):
    """
    Builds the variables that would be used in in p2a_impacts.resolve_rules
    to the point of accessing the climate explorer database, but instead of evaluating
    a rule it writes the paths for the files used to a file.
    """
    logger = setup_logging(log_level)
    region = get_region(region, url)

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
            logger.info("{}, rule will be excluded".format(e))
            continue

        # check region var
        if region_var:
            region_variable = region_var

        # add unique variables to set
        for name, values in vars.items():
            if name not in variables.keys():
                variables[name] = values

    logger.info("Collecting variables")
    Session = sessionmaker(create_engine(connection_string))
    sesh = Session()

    # get file paths by date_range
    file_paths = set()
    for date in date_range:
        logger.info("Getting file paths for {}".format(date))

        # get file paths by variable
        for name, values in variables.items():
            file_paths.update(
                get_paths_by_var(sesh, values, ensemble, date, region, logger)
            )

    # write paths to file
    logger.info("Writing file paths to {}".format(output_file))
    with open(output_file, "a") as fout:
        for file_ in file_paths:
            fout.write(file_ + "\n")


def get_paths_by_var(sesh, variables, ensemble, date_range, region, logger):
    """Given a variable name get the required file's path by querying the CE backend.
    """
    logger.info("")
    logger.info("Translating variables for query")
    query_args = translate_args(
        variables["variable"],
        variables["time_of_year"],
        variables["temporal"],
        variables["spatial"],
        variables["percentile"],
        region,
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

    paths = set()
    [paths.update(query_files(sesh, model, query_args)) for model in models]
    logger.info("Getting file paths for {}".format(var_name))
    return paths


def query_files(sesh, model, query_args):
    """Return the desired file names for a particular climate model"""
    id_generators = [
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
    file_names = set()
    for ids in id_generators:
        for model_id in list(ids):
            data_file = (
                sesh.query(DataFile).filter(DataFile.unique_id == model_id).one()
            )

            if data_file is not None:
                file_names.add(data_file.filename)

    return file_names


if __name__ == "__main__":
    file_collection()
