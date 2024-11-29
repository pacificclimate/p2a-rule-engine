import os
import click
from p2a_impacts.utils import (
    create_session,
    setup_logging,
)
from cell_resolver import resolve_rules_by_cell
from cell_utils import save_to_netcdf
from region_rule_aggregator import aggregate_results_by_region


@click.command()
@click.option("-c", "--csv", help="CSV file containing rules", required=True)
@click.option(
    "-m",
    "--mask",
    help="Region-union NetCDF file to subset climate vars",
    required=True,
)
@click.option("-r", "--region-masks", help="Region masks", required=True)
@click.option(
    "-d",
    "--date-range",
    help="30-year period for data",
    type=click.Choice(["hist", "2030", "2050", "2080"]),
    default="2080",
)
@click.option(
    "-x",
    "--connection-string",
    help="Database connection string",
    required=True,
)
@click.option(
    "-e", "--ensemble", help="Ensemble name filter for data files", default="p2a_rules"
)
@click.option("-t", "--thredds", help="Target data from Thredds server", is_flag=True)
@click.option(
    "-o",
    "--output-dir",
    help="Directory to save the JSON files for each region",
    default="outputs",
)
@click.option(
    "-u",
    "--url",
    help="Geoserver URL",
    default="https://beehive.pacificclimate.org/plan2adapt/bc_regions/ows",
)
@click.option(
    "-l",
    "--log-level",
    help="Logging level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
)
def process(
    csv,
    mask,
    region_masks,
    date_range,
    connection_string,
    ensemble,
    thredds,
    output_dir,
    url,
    log_level,
):
    logger = setup_logging(log_level)

    # Resolve rules per cell
    logger.info("Resolving rules per cell")
    sesh = create_session(connection_string)
    rules_by_cell = resolve_rules_by_cell(
        csv, mask, date_range, ensemble, sesh, thredds, log_level
    )
    output_file = os.path.join(output_dir, "rules_per_cell.nc")
    save_to_netcdf(rules_by_cell, output_file, mask)

    # Aggregate results by region
    logger.info("Aggregating results by region")
    aggregate_results_by_region(
        rules_by_cell, region_masks, mask, output_dir, date_range
    )

    logger.info("Workflow complete")


if __name__ == "__main__":
    process()
