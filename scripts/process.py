"""
The purpose of this script is to run the rule resolver with some parameters
that could be expected from the p2a front end.
"""
import sys
import click
import json

from p2a_impacts.resolver import resolve_rules
from p2a_impacts.utils import get_region, REGIONS, create_session


@click.command()
@click.option("-c", "--csv", help="CSV file containing rules", required=True)
@click.option(
    "-d",
    "--date-range",
    help="30 year period for data",
    type=click.Choice(["2020", "2050", "2080"]),
    default="2080",
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
    default="postgresql://ce_meta_ro@db3.pcic.uvic.ca/ce_meta_12f290b63791",
)
@click.option(
    "-e", "--ensemble", help="Ensemble name filter for data files", default="p2a_rules",
)
@click.option(
    "-t", "--thredds", help="Target data from thredds server", is_flag=True,
)
@click.option(
    "-l",
    "--log-level",
    help="Logging level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
)
def process(
    csv, date_range, region, url, connection_string, ensemble, thredds, log_level
):
    region = get_region(region, url)

    if not region:
        raise Exception("{} region was not found".format(region))

    sesh = create_session(connection_string)
    rules = resolve_rules(csv, date_range, region, ensemble, sesh, thredds, log_level,)
    json.dump(rules, sys.stdout)


if __name__ == "__main__":
    process()
