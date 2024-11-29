import os
import json
import logging
import xarray as xr
import numpy as np

logger = logging.getLogger("scripts")


def save_to_netcdf(results, output_file, mask_file):
    # Open the mask file to get coordinates
    with xr.open_dataset(mask_file) as mask_ds:
        mask_ds = standardize_coordinates(mask_ds)
        dataset = xr.Dataset()

        # Add the latitude and longitude coordinates from the mask file
        dataset.coords["latitude"] = mask_ds.coords["latitude"]
        dataset.coords["longitude"] = mask_ds.coords["longitude"]

        # Add each rule result to the dataset
        for rule_name, rule_result in results.items():
            dataset[rule_name] = (("latitude", "longitude"), rule_result)

    # Save to NetCDF
    dataset.to_netcdf(output_file)
    logger.info(f"NetCDF saved to {output_file}")


def save_to_json(output_dir, region_name, date_range, region_results):
    json_output_file = os.path.join(output_dir, f"{region_name}_{date_range}.json")
    with open(json_output_file, "w") as json_file:
        json.dump(region_results, json_file, indent=2)

    logger.info(f"Results for region {region_name} saved to {json_output_file}")


def ensure_ascending_latitude(dataset):
    if dataset.coords["latitude"][0] > dataset.coords["latitude"][-1]:
        return dataset.reindex(latitude=dataset.latitude[::-1])
    return dataset


def ensure_dataset_alignment(dataset):
    dataset_processed = dataset.fillna(0).astype(np.uint8)
    dataset_processed = ensure_ascending_latitude(dataset_processed)

    return dataset


def standardize_coordinates(dataset):

    # Standardize coordinate dimension names to 'latitude' and 'longitude'.
    coord_mapping = {
        "lat": "latitude",
        "latitude": "latitude",
        "latitudes": "latitude",
        "lon": "longitude",
        "long": "longitude",
        "longitude": "longitude",
        "longitudes": "longitude",
    }

    for original, standardized in coord_mapping.items():
        if original in dataset.coords:
            dataset = dataset.rename({original: standardized})
    dataset = ensure_ascending_latitude(dataset)
    return dataset
