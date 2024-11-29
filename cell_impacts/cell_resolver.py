import logging
from functools import partial
import xarray as xr
from modelmeta import DataFile

from cell_evaluator import evaluate_rule
from cell_utils import standardize_coordinates
from fetch_cell_data import get_gridded_variables
from p2a_impacts.fetch_data import get_dict_val, read_csv
from p2a_impacts.parser import build_parse_tree


logger = logging.getLogger("scripts")


def resolve_rules_by_cell(
    csv, mask_file, date_range, ensemble, sesh, thredds, log_level="INFO"
):
    """
    Resolve rules per grid cell and prepare data for evaluation, filtering with a region mask.

    Args:
        csv (str): Path to the CSV file containing rules.
        mask_file (str): Path to the NetCDF mask file.
        date_range (str): Time period for the data.
        ensemble (str): Ensemble filter for fetching climate data.
        sesh: Database session object for fetching data.
        thredds (bool): Whether to use the THREDDS server for data retrieval.
        log_level (str): Logging level.

    Returns:
        dict: Results of rule evaluation per cell.
    """

    logger.info(f"Loading region mask from {mask_file}")
    mask_ds = xr.open_dataset(mask_file)
    mask_ds = standardize_coordinates(mask_ds)
    mask = mask_ds["all_regions"].values  # Assumes 'all_regions' is the mask variable
    logger.debug(f"Region mask shape: {mask.shape}")

    logger.info(f"Reading {csv}")
    rules = read_csv(csv)

    logger.info("Building parse trees")
    parse_trees = {}
    variables = {}
    for rule, condition in rules.items():
        try:
            parse_trees[rule], vars, _ = build_parse_tree(
                condition
            )  # `region_var` not needed
        except SyntaxError as e:
            logger.warning("{}, rule will be excluded".format(e))
            continue

        # Add unique vars to the variable list
        for name, values in vars.items():
            if name not in variables:
                variables[name] = values

    logger.info("Collecting and filtering variables")
    collected_variables = {}
    missing_variables = []
    missing_variables_file = "missing_variables.txt"
    for name, values in variables.items():
        try:
            gridded_var = get_gridded_variables(
                sesh, values, ensemble, date_range, thredds, mask
            )
            if gridded_var is not None:
                collected_variables[name] = gridded_var
            else:
                missing_variables.append(name)
        except Exception as e:
            logger.warning(f"Error fetching {name}: {e}")
            missing_variables.append(name)

    logger.info(f"Collected {len(collected_variables)}/{len(variables)} variables")

    if missing_variables:
        logger.warning(f"Missing variables: {', '.join(missing_variables)}")
        # Write missing variables to a text file, one per line
        with open(missing_variables_file, "w") as f:
            f.writelines(f"{var}\n" for var in missing_variables)
            logger.info(
                f"Missing variables have been logged to {missing_variables_file}"
            )
        return None
    else:
        logger.info("All variables were successfully collected.")

    # Prepare evaluators
    variable_getter = partial(get_dict_val, collected_variables)
    rule_getter = partial(get_dict_val, parse_trees)

    # Evaluate rules per cell
    logger.info("Evaluating rules per cell")
    results = {}
    failed_rules = []  # Track failed rules
    failed_rules_file = "failed_rules.txt"

    for rule_id, rule_tree in parse_trees.items():
        try:
            logger.info(f"Evaluating {rule_id}")
            results[rule_id] = evaluate_rule(rule_tree, rule_getter, variable_getter)
        except Exception as e:
            logger.warning(f"Error evaluating {rule_id}: {e}")
            failed_rules.append(rule_id)

    logger.info(f"Resolved {len(results)}/{len(parse_trees)} rules")

    # Log failed rules to a file, one per line
    if failed_rules:
        logger.warning(f"Failed rules: {', '.join(failed_rules)}")
        with open(failed_rules_file, "w") as f:
            f.writelines(f"{rule}\n" for rule in failed_rules)
            logger.info(f"Failed rules have been logged to {failed_rules_file}")
    else:
        logger.info("All rules were successfully evaluated.")

    return results
