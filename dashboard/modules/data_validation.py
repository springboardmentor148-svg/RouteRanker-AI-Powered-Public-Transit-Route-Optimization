import pandas as pd


def validate_dataset(dataframe, dataset_name, required_columns=None):
    """Validate basic dataset structure and required columns."""

    errors = []

    if dataframe is None or dataframe.empty:
        errors.append("Dataset is empty.")
        return errors

    if dataframe.columns.duplicated().any():
        errors.append("Duplicate column names found.")

    if required_columns:
        missing_columns = [
            column for column in required_columns
            if column not in dataframe.columns
        ]

        if missing_columns:
            errors.append(
                f"Missing required columns: {missing_columns}"
            )

    return errors


def validate_route_identifiers(dataframe):
    """Check route identifiers using city and route_id together."""

    required = ["city", "route_id"]

    errors = validate_dataset(
        dataframe,
        "route dataset",
        required
    )

    if errors:
        return errors

    if dataframe[required].isna().any().any():
        errors.append("Missing city or route_id values.")

    duplicate_routes = dataframe.duplicated(
        subset=["city", "route_id"]
    ).sum()

    if duplicate_routes > 0:
        errors.append(
            f"{duplicate_routes} duplicate city-route combinations found."
        )

    return errors


def get_validation_summary(datasets):
    """Generate a validation summary for all loaded datasets."""

    results = []

    for name, dataframe in datasets.items():
        errors = validate_dataset(dataframe, name)

        results.append({
            "Dataset": name,
            "Status": "Passed" if not errors else "Failed",
            "Errors": "; ".join(errors) if errors else "None"
        })

    return pd.DataFrame(results)
