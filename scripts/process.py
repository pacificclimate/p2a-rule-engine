"""
The purpose of this script is to run the rule resolver with some parameters
that could be expected from the p2a front end.
"""
import sys
from argparse import ArgumentParser
import json

from p2a_impacts.resolver import resolve_rules
from p2a_impacts.utils import get_region, REGIONS


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-c", "--csv", help="CSV file containing rules", required=True)
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
    parser.add_argument(
        "-l",
        "--log-level",
        help="Logging level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
    )
    args = parser.parse_args()
    region = get_region(args.region, args.url)

    if not region:
        raise Exception("{} region was not found".format(args.region))

    rules = resolve_rules(
        args.csv,
        args.date_range,
        region,
        args.ensemble,
        args.connection_string,
        args.log_level,
    )
    json.dump(rules, sys.stdout)
