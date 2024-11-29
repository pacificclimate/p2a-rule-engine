import logging
import json
import numpy as np
import xarray as xr
import numpy.ma as ma

from ce.api.util import (
    search_for_unique_ids,
    open_nc,
    time_slice_array,
    apply_thredds_root,
)
from ce.api.models import models
import modelmeta as mm
from p2a_impacts.fetch_data import (
    translate_args,
    get_models,
    get_nffd,
)


logger = logging.getLogger("scripts")



def apply_mask(data, mask):
    # Replace NaN in the mask with 0 (ocean or out-of-bounds regions)
    cleaned_mask = np.nan_to_num(mask, nan=0)

    # Apply the mask (only mask where the value is not 1)
    masked_data = ma.masked_where(cleaned_mask != 1, data)
    return masked_data


def compute_percentiles(stacked_data, percentile, logger):
    # Computes percentiles for 2D or 3D stacked data while handling NaNs.
    logger.debug(f"Input array shape: {stacked_data.shape}")
    logger.debug(f"Total elements: {stacked_data.size}")
    logger.debug(f"NaN count: {np.isnan(stacked_data).sum()}")
    logger.debug(
        f"NaN percentage: {np.isnan(stacked_data).sum() / stacked_data.size * 100:.2f}%"
    )

    if stacked_data.ndim == 2:
        logger.debug("Detected 2D grid (latitude × longitude)")
        # Return the grid itself, as percentiles are not applicable for 2D data
        return stacked_data

    elif stacked_data.ndim == 3:
        logger.debug("Detected 3D grid (models × latitude × longitude)")
        # Mask invalid (NaN) values
        masked_data = np.ma.masked_invalid(stacked_data)
        logger.debug(f"Masked data count: {masked_data.count()}")

        if masked_data.count() == 0:
            logger.warning("No valid data available for percentile calculation")
            # Return a grid of NaNs matching the spatial dimensions
            return np.full(stacked_data.shape[1:], np.nan)

        try:
            # Compute percentiles along the first axis (model dimension)
            results = np.percentile(masked_data, percentile, axis=0)
            logger.debug(f"Percentile {percentile} calculated for 3D grid")
            return results
        except Exception as e:
            logger.error(f"Percentile calculation failed: {e}")
            return None
    else:
        logger.error(f"Unsupported data dimensions: {stacked_data.ndim}")
        raise ValueError("Input data must be 2D or 3D")
        return None


def multistats_grid(
    sesh,
    ensemble_name="ce_files",
    model_list=None,
    emission="",
    time=0,
    mask=None,
    variable="",
    timescale="",
    climatological_statistic="mean",
    is_thredds=False,
    percentile=None,
    target="mean",
):
    """
    Compute grid-cell-level statistics for multiple variables across models.

    Args:
        sesh (sqlalchemy.orm.session.Session): A database session object.
        ensemble_name (str): Ensemble name filter.
        model_list (list): List of climate models to process.
        emission (str): Emission scenario.
        time (int): Time index (0-based).
        mask (numpy.ndarray): All Regions mask for filtering data.
        variable (str or list): Climate variable(s) to extract.
        timescale (str): Temporal resolution (e.g., "monthly").
        climatological_statistic (str): Statistic to calculate (e.g., "mean").
        is_thredds (bool): Use THREDDS server file paths.
        percentile (float): Percentile to compute
        target (str): Optional. Temperature target, one of 'min', 'max', 'mean'.

    Returns:
        np.ndarray: Percentile values aggregated across models for the variable(s).
    """
    if not model_list:
        logger.debug("Model list is empty. No processing will be performed.")
        return None

    if isinstance(variable, str):
        variable = [variable]  # Ensure variable is a list

    # Mapping for temperature variables if target is specified
    target_variable_mapping = {
        "min": "tasmin",
        "max": "tasmax",
        "mean": "tas",
    }

    is_temp = {"tasmin", "tasmax"}.issubset(variable)
    grids, processed_vars = [], []

    is_monthly_temp = False
    if is_temp:
        # Handle temperature-specific logic
        is_monthly_temp = timescale == "monthly"
        if is_monthly_temp:
            temp_variables = [
                "tasmin",
                "tasmax",
            ]  # Compute mean of tasmin and tasmax for `tas`
        else:
            temp_variables = [
                target_variable_mapping[target]
            ]  # Single target variable for temperature
        processed_vars.extend(temp_variables)
    else:
        processed_vars.extend(variable)  # Non-temperature variables

    logger.debug(f"Processing variable(s): {', '.join(processed_vars)}")
    logger.debug(f"Processing model(s): {', '.join(model_list)}")
    # Iterate over processed variables
    for var in processed_vars:
        for model in model_list:
            try:
                # Fetch unique IDs for the current model and variable
                unique_ids = list(
                    search_for_unique_ids(
                        sesh,
                        ensemble_name=ensemble_name,
                        model=model,
                        emission=emission,
                        variable=var,
                        time=time,
                        timescale=timescale,
                        climatological_statistic=climatological_statistic,
                    )
                )
                if not unique_ids:
                    logger.warning(
                        f"No data files found for {var} ({model}, {emission}) in ensemble {ensemble_name}"
                    )
                    continue

                # Query DataFile objects by unique ID
                data_files = (
                    sesh.query(mm.DataFile)
                    .filter(mm.DataFile.unique_id.in_(unique_ids))
                    .all()
                )

                for df in data_files:
                    try:
                        resource = (
                            df.filename
                            if not is_thredds
                            else apply_thredds_root(df.filename)
                        )
                        with open_nc(resource) as nc:
                            # Extract the array for the specified variable, time

                            logger.debug(
                                f"Data shape before slicing: {nc.variables[var][:].shape}"
                            )
                            data = time_slice_array(
                                nc.variables[var], time, nc, resource, var
                            )
                            assert (
                                data.shape == mask.shape
                            ), f"Mismatch: data shape {data.shape}, mask shape {mask.shape}"

                            logger.debug(f"Sliced data shape: {data.shape}")
                            # Create an xarray DataArray with whatever coordinates are available
                            coords = {}
                            if "lat" in nc.variables:
                                lat_coords = nc.variables["lat"][:]
                                if lat_coords[0] > lat_coords[-1]:
                                    lat_coords = lat_coords[::-1]
                                coords["latitude"] = lat_coords
                            elif "latitude" in nc.variables:
                                lat_coords = nc.variables["latitude"][:]
                                if lat_coords[0] > lat_coords[-1]:
                                    lat_coords = lat_coords[::-1]
                                coords["latitude"] = lat_coords

                            # Similar logic for longitude
                            if "lon" in nc.variables:
                                lon_coords = nc.variables["lon"][:]
                                coords["longitude"] = lon_coords
                            elif "longitude" in nc.variables:
                                lon_coords = nc.variables["longitude"][:]
                                coords["longitude"] = lon_coords

                            xr_data = xr.DataArray(
                                data=data,
                                dims=list(
                                    coords.keys()
                                ),  # Use the coordinate keys as dimensions
                                coords=coords,  # Use the extracted coordinates
                            )
                            logger.debug(
                                f"Variable: {var}, xr_data Shape: {xr_data.shape}"
                            )
                            logger.debug(f"Unique mask values: {np.unique(mask)}")
                            logger.debug(
                                f"{var} before masking NaN: {np.isnan(data).sum()}, NNaN: {np.sum(~np.isnan(data))}"
                            )
                            # Apply mask
                            masked_data = apply_mask(xr_data, mask)
                            logger.debug(
                                f"{var} after masking NaN: {np.isnan(masked_data).sum()}, NNaN: {np.sum(~np.isnan(masked_data))}"
                            )
                            valid_cells = np.sum(~np.isnan(masked_data))
                            total_cells = data.size
                            logger.debug(
                                f"Valid cells after masking: {valid_cells}/{total_cells}"
                            )
                            if valid_cells == 0:
                                logger.error("All data excluded by the mask.")
                                raise ValueError("The mask excludes all data.")

                            grids.append(masked_data)
                    except Exception as e:
                        logger.error(f"Error processing file {df.filename}: {e}")

            except Exception as e:
                logger.error(
                    f"Error processing model '{model}' for variable '{var}': {e}"
                )
                sesh.rollback()
                continue
    if is_monthly_temp:
        if len(grids) == 2:
            # Compute the mean of tasmin and tasmax grids directly using np.mean
            stacked_data = np.mean(grids, axis=0)
            logger.info(
                "Computed tas (mean of tasmin and tasmax) for monthly temperature."
            )
        else:
            logger.warning(
                "Expected 2 grids for tasmin and tasmax, but found a different number."
            )
            return None

    else:
        if grids:
            stacked_data = ma.stack(grids, axis=0)
        else:
            logger.warning("No data grids available for stacking.")
            return None

    return compute_percentiles(stacked_data, percentile, logger)


def get_gridded_variables(sesh, variables, ensemble, date_range, thredds, mask):

    logger.info("Translating variables for query")
    query_args = translate_args(
        variables["variable"],
        variables["time_of_year"],
        variables["temporal"],
        variables["spatial"],
        variables["percentile"],
        {"the_geom": "placeholder_geometry"},
        date_range,
        ensemble,
        thredds,
    )
    logger.info("Translated query arguments:\n%s", json.dumps(query_args, indent=2))
    logger.info("Collecting models for variable")
    model_list = get_models(sesh, variables["percentile"], ensemble)

    if not model_list:
        logger.warning(
            f"No models found for ensemble '{ensemble}' with percentile '{variables['percentile']}'"
        )
        return None

    logger.debug(f"Processing query var(s): {variables['variable']}")
    try:
        # Fetch gridded results using multistats_grid
        stats = multistats_grid(
            sesh,
            ensemble_name=query_args["ensemble_name"],
            model_list=model_list,
            emission=query_args["emission"],
            time=query_args["time"],
            mask=mask,
            variable=query_args["variable"],
            timescale=query_args["timescale"],
            climatological_statistic=query_args["cell_method"],
            is_thredds=query_args["thredds"],
            percentile=query_args["percentile"],
            target=query_args["spatial"],
        )
        return stats
    except Exception as e:
        logger.warning(f"Error fetching variables: {e}")
        return None
