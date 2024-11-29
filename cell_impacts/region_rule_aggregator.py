import os
import logging
import numpy as np
import xarray as xr
from cell_utils import (
    ensure_dataset_alignment,
    standardize_coordinates,
    save_to_json,
)

logger = logging.getLogger("scripts")


def aggregate_results_by_region(
    rules_by_cell, region_masks, mask, output_dir, date_range
):
    # Load region masks from the NetCDF file
    with xr.open_dataset(region_masks) as region_ds:
        region_masks = {
            region: standardize_coordinates(region_ds[region])
            for region in region_ds.data_vars
        }

    # Obtain coordinate information from all-regions mask
    with xr.open_dataset(mask) as ref_ds:
        ref_ds = standardize_coordinates(ref_ds)
        latitudes = ref_ds["latitude"]
        longitudes = ref_ds["longitude"]

    # Convert rule layers to xarray DataArrays
    rules_by_cell = {
        rule_name: standardize_coordinates(
            xr.DataArray(
                data=rule_array,
                coords={"latitude": latitudes, "longitude": longitudes},
                dims=["latitude", "longitude"],
            )
        )
        for rule_name, rule_array in rules_by_cell.items()
    }

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Compute and save results for each region
    for region_name, region_mask in region_masks.items():
        logger.debug(f"Processing region: {region_name}")

        # Convert region mask to binary and ensure correct orientation
        region_mask_processed = ensure_dataset_alignment(region_mask)

        logger.debug(
            f"Unique values in region mask '{region_name}': {np.unique(region_mask_processed.values)}"
        )

        total_cells = region_mask_processed.sum().item()

        if total_cells == 0:
            logger.warning(f"Region {region_name} has no valid cells. Skipping.")
            continue

        region_results = {}
        for rule_name, rule_layer in rules_by_cell.items():
            # Convert rule layer to binary and ensure correct orientation
            rule_layer_processed = ensure_dataset_alignment(rule_layer)

            logger.debug(
                f"Unique values in rule '{rule_name}': {np.unique(rule_layer_processed.values)}"
            )

            # Align the rule layer and region mask
            rule_layer_aligned, region_mask_aligned = xr.align(
                rule_layer_processed, region_mask_processed, join="inner"
            )

            if rule_layer_aligned.shape != region_mask_aligned.shape:
                logger.error(
                    f"Shape mismatch for rule '{rule_name}' and region '{region_name}'."
                )
                region_results[rule_name] = 0.0
                continue

            # Skip rules with no valid cells
            if not rule_layer_aligned.any():
                logger.debug(
                    f"Skipping rule '{rule_name}' as it contains no True values."
                )
                region_results[rule_name] = 0.0
                continue

            # Element-wise multiplication and sum
            matching_cells = (rule_layer_aligned * region_mask_aligned).sum().item()

            # Calculate percentage and convert to float
            percentage = float((matching_cells / total_cells) * 100)

            # Add result
            region_results[rule_name] = percentage

            logger.debug(
                f"Region '{region_name}', Rule '{rule_name}': Matching cells: {matching_cells}, "
                f"Total cells: {total_cells}, Percentage: {percentage}"
            )

        # Save results to JSON
        save_to_json(output_dir, region_name, date_range, region_results)

    logger.info("Region-rule aggregation complete")
