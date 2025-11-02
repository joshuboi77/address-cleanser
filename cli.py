"""
Command-line interface for the Address Cleanser tool.

This module provides a CLI interface using Click for processing addresses
in CSV, JSON, and Excel formats.
"""

import atexit
import csv
import io
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# In PyInstaller, prepare to suppress cleanup errors
# Store original stderr so logging can still work
if hasattr(sys, "frozen") and sys.frozen:
    import io

    # Store original stderr for logging
    sys._original_stderr = sys.stderr
    sys._null_stderr = io.StringIO()

    # Track if we've completed successfully
    sys._cleanup_mode = False

    # Override excepthook to suppress cleanup errors
    _original_excepthook = sys.excepthook

    def _suppress_cleanup_exceptions(exc_type, exc_value, exc_traceback):
        """Suppress exceptions during cleanup phase."""
        # If we're in cleanup mode, suppress all exceptions silently
        if getattr(sys, "_cleanup_mode", False):
            # Check if it's a cleanup-related error
            error_str = str(exc_value) if exc_value else ""
            if any(
                keyword in error_str for keyword in ["base_library.zip", "_MEI", "No such file"]
            ):
                # Silently ignore cleanup errors
                return
        # For non-cleanup errors, use original handler
        _original_excepthook(exc_type, exc_value, exc_traceback)

    sys.excepthook = _suppress_cleanup_exceptions

import click
import pandas as pd
from tqdm import tqdm

from src.formatter import create_formatted_address_result
from src.parser import handle_edge_cases, parse_address
from src.utils import (
    calculate_processing_stats,
    combine_address_columns,
    detect_address_columns,
    ensure_directory_exists,
    setup_logging,
    validate_file_extension,
)
from src.validator import validate_address


def _suppress_cleanup_errors():
    """
    Suppress PyInstaller cleanup errors during shutdown.

    This is a workaround for a known PyInstaller onefile mode issue where
    the temporary directory is deleted while Python is still trying to
    access modules during cleanup, causing FileNotFoundError.

    The error is cosmetic and occurs after successful execution, so we
    suppress stderr during cleanup to prevent error messages.
    """
    # Only suppress if we're in a PyInstaller environment
    if hasattr(sys, "frozen") and sys.frozen:
        # Mark that we're entering cleanup mode
        sys._cleanup_mode = True

        # Replace stderr with a null device during cleanup
        if hasattr(sys, "_null_stderr"):
            sys.stderr = sys._null_stderr
        else:
            sys.stderr = io.StringIO()


# Register cleanup handler to suppress errors during exit
atexit.register(_suppress_cleanup_errors)


@click.group()
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Set the logging level",
)
@click.option("--log-file", help="Log file path (optional)")
@click.pass_context
def cli(ctx, log_level, log_file):
    """Address Cleanser - Parse, validate, and format US addresses."""
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Set up logging
    logger = setup_logging(log_level, log_file)
    ctx.obj["logger"] = logger

    logger.info(f"Address Cleanser started with log level: {log_level}")


@cli.command()
@click.option("--input", "-i", required=True, help="Input CSV file path")
@click.option("--output", "-o", required=True, help="Output file path")
@click.option(
    "--format",
    "-f",
    default="csv",
    type=click.Choice(["csv", "json", "excel"]),
    help="Output format",
)
@click.option(
    "--address-column",
    "-c",
    default=None,
    help="Name of the address column in input CSV (auto-detected if not specified)",
)
@click.option(
    "--address-columns",
    "-C",
    help="Comma-separated list of address columns to combine (e.g., 'Address,City,State,Zip')",
)
@click.option(
    "--preserve-columns",
    "-p",
    is_flag=True,
    default=False,
    help="Preserve all original CSV columns in output",
)
@click.option(
    "--auto-combine",
    "-a",
    is_flag=True,
    default=False,
    help="Auto-detect and combine separate address columns",
)
@click.option("--report", "-r", help="Validation report file path (optional)")
@click.option("--chunk-size", default=1000, help="Process addresses in chunks of this size")
# CSV formatting options
@click.option("--csv-delimiter", default=",", help="CSV delimiter character (default ',')")
@click.option(
    "--csv-encoding",
    default="utf-8",
    help="File encoding for CSV/JSON/Excel (default 'utf-8'; use 'utf-8-sig' for Excel on Windows)",
)
@click.option(
    "--csv-quote",
    type=click.Choice(["minimal", "all", "nonnumeric", "none"]),
    default="minimal",
    help="CSV quoting strategy (default 'minimal')",
)
@click.option(
    "--csv-newline",
    type=click.Choice(["system", "lf", "crlf"]),
    default="system",
    help="Line endings for CSV output (default 'system')",
)
@click.option(
    "--excel-friendly",
    is_flag=True,
    default=False,
    help="Shorthand: encoding utf-8-sig + CRLF + quote all for best Excel compatibility",
)
@click.option(
    "--prune-empty-cleaned",
    is_flag=True,
    default=False,
    help="Remove cleaned_* columns that are completely empty (off by default)",
)
@click.option(
    "--update-in-place",
    is_flag=True,
    default=False,
    help="Mirror input structure: keep same columns, update values with cleaned data (perfect for client returns)",
)
@click.pass_context
def batch(
    ctx,
    input,
    output,
    format,
    address_column,
    address_columns,
    preserve_columns,
    auto_combine,
    report,
    chunk_size,
    csv_delimiter,
    csv_encoding,
    csv_quote,
    csv_newline,
    excel_friendly,
    prune_empty_cleaned,
    update_in_place,
):
    """Process addresses from a CSV file in batch."""
    logger = ctx.obj["logger"]

    try:
        # Validate input file
        if not validate_file_extension(input, [".csv"]):
            logger.error(f"Invalid input file format: {input}. Expected CSV file.")
            sys.exit(1)

        if not os.path.exists(input):
            logger.error(f"Input file does not exist: {input}")
            sys.exit(1)

        # Process the file
        # Note: update_in_place requires original_df, so we preserve columns
        # Also enable auto_combine for update_in_place to parse complete addresses
        results, original_df = process_csv_file(
            input,
            address_column,
            address_columns,
            preserve_columns or update_in_place,
            auto_combine or update_in_place,
            chunk_size,
            logger,
        )

        # Write output with CSV options
        csv_options = {
            "delimiter": csv_delimiter,
            "encoding": csv_encoding,
            "quote": csv_quote,
            "newline": csv_newline,
            "excel_friendly": excel_friendly,
            "prune_empty_cleaned": prune_empty_cleaned,
            "update_in_place": update_in_place,
        }
        write_output(
            results,
            output,
            format,
            logger,
            original_df if (preserve_columns or update_in_place) else None,
            csv_options=csv_options,
        )

        # Write report if requested
        if report:
            write_validation_report(results, report, logger)

        # Print summary
        stats = calculate_processing_stats(results)
        logger.info(
            f"Processing complete. {stats['total_processed']} addresses processed, "
            f"{stats['successful']} successful ({stats['success_rate']}% success rate)"
        )

    except Exception as e:
        logger.error(f"Error processing batch file: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option("--single", "-s", required=True, help="Single address to process")
@click.option(
    "--format",
    "-f",
    default="json",
    type=click.Choice(["csv", "json", "excel"]),
    help="Output format",
)
@click.option(
    "--output", "-o", help="Output file path (optional, prints to console if not specified)"
)
@click.pass_context
def single(ctx, single, format, output):
    """Process a single address."""
    logger = ctx.obj["logger"]

    try:
        # Process the single address
        result = process_single_address(single, logger)

        if output:
            # Write to file
            write_output([result], output, format, logger)
            logger.info(f"Result written to {output}")
        else:
            # Print to console
            if format == "json":
                print(json.dumps(result, indent=2))
            else:
                print(f"Original: {result['original']}")
                print(f"Formatted: {result['single_line']}")
                print(f"Valid: {result['valid']}")
                print(f"Confidence: {result['confidence']:.1f}%")
                if result["issues"]:
                    print(f"Issues: {', '.join(result['issues'])}")

    except Exception as e:
        logger.error(f"Error processing single address: {str(e)}")
        sys.exit(1)


def process_csv_file(
    input_file: str,
    address_column: Optional[str],
    address_columns: Optional[str],
    preserve_columns: bool,
    auto_combine: bool,
    chunk_size: int,
    logger,
) -> Tuple[List[Dict[str, Any]], Optional[pd.DataFrame]]:
    """
    Process addresses from a CSV file with enhanced column preservation.

    Args:
        input_file: Path to input CSV file
        address_column: Name of the address column (None for auto-detect)
        address_columns: Comma-separated list of columns to combine
        preserve_columns: Whether to preserve original columns
        auto_combine: Auto-detect and combine separate address columns
        chunk_size: Number of addresses to process at once

    Returns:
        Tuple of (list of processing results, original DataFrame if preserving columns)
    """
    logger.info(f"Reading CSV file: {input_file}")

    # Read CSV file
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        logger.error(f"Error reading CSV file: {str(e)}")
        raise

    # Determine address column(s)
    actual_address_column = None
    combined_address_series = None

    # If explicit columns provided, combine them
    if address_columns:
        columns_to_combine = [col.strip() for col in address_columns.split(",")]
        missing_cols = [col for col in columns_to_combine if col not in df.columns]
        if missing_cols:
            logger.error(
                f"Address columns not found: {missing_cols}. Available columns: {list(df.columns)}"
            )
            raise ValueError(f"Address columns not found: {missing_cols}")
        logger.info(f"Combining address columns: {columns_to_combine}")
        combined_address_series = combine_address_columns(df, columns_to_combine)
        actual_address_column = "_combined_address"
        df[actual_address_column] = combined_address_series

    # Auto-detect and combine if enabled
    elif auto_combine and not address_column:
        detected_cols = detect_address_columns(df)
        if detected_cols and len(detected_cols) > 1:
            logger.info(f"Auto-detected address columns: {detected_cols}")
            combined_address_series = combine_address_columns(df, detected_cols)
            actual_address_column = "_combined_address"
            df[actual_address_column] = combined_address_series
        elif detected_cols and len(detected_cols) == 1:
            actual_address_column = detected_cols[0]
            logger.info(f"Auto-detected single address column: {actual_address_column}")

    # Use specified column or default
    if not actual_address_column:
        if address_column:
            actual_address_column = address_column
        else:
            # Try default "address" column
            if "address" in df.columns:
                actual_address_column = "address"
            else:
                # Try case-insensitive match
                columns_lower = [col.lower() for col in df.columns]
                if "address" in columns_lower:
                    actual_address_column = df.columns[columns_lower.index("address")]
                    logger.info(
                        f"Using case-insensitive match: '{actual_address_column}' for 'address'"
                    )
                else:
                    logger.error(f"No address column found. Available columns: {list(df.columns)}")
                    raise ValueError("No address column found. Use --address-column to specify.")

    # Check if address column exists
    if actual_address_column not in df.columns:
        logger.error(
            f"Address column '{actual_address_column}' not found in CSV. "
            f"Available columns: {list(df.columns)}"
        )
        raise ValueError(f"Address column '{actual_address_column}' not found")

    # Get addresses (preserve alignment)
    addresses_series = df[actual_address_column]
    total_rows = len(addresses_series)
    logger.info(f"Found {total_rows} rows; processing address column with alignment preserved")

    results = []

    def _empty_result(orig: Any, issue: str) -> Dict[str, Any]:
        return {
            "original": (
                "" if (orig is None or (isinstance(orig, float) and pd.isna(orig))) else str(orig)
            ),
            "parsed": {},
            "formatted": {},
            "single_line": "",
            "multi_line": [],
            "confidence": 0.0,
            "valid": False,
            "issues": [issue],
            "address_type": "Empty",
        }

    # Iterate in chunks but over the full aligned series
    for start in tqdm(range(0, total_rows, chunk_size), desc="Processing addresses"):
        end = min(start + chunk_size, total_rows)
        chunk_results = []
        for addr in addresses_series.iloc[start:end]:
            if pd.isna(addr) or (isinstance(addr, str) and addr.strip() == ""):
                chunk_results.append(_empty_result(addr, "Missing address"))
                continue
            try:
                chunk_results.append(process_single_address(str(addr), logger))
            except Exception as e:
                logger.warning(f"Error processing address '{addr}': {str(e)}")
                chunk_results.append(
                    {
                        "original": str(addr),
                        "parsed": {},
                        "formatted": {},
                        "single_line": "",
                        "multi_line": [],
                        "confidence": 0.0,
                        "valid": False,
                        "issues": [f"Processing error: {str(e)}"],
                        "address_type": "Error",
                    }
                )
        results.extend(chunk_results)

    # Return original DataFrame if preserving columns
    original_df = df.copy() if preserve_columns else None
    # Remove temporary combined column from original if it exists
    if original_df is not None and "_combined_address" in original_df.columns:
        original_df = original_df.drop(columns=["_combined_address"])

    return results, original_df


def process_single_address(address: str, logger) -> Dict[str, Any]:
    """
    Process a single address through the complete pipeline.

    Args:
        address: Address string to process
        logger: Logger instance

    Returns:
        Complete processing result
    """
    # Pre-process address
    processed_address = handle_edge_cases(address)

    # Parse address
    parsed_result = parse_address(processed_address)

    # Normalize and validate address
    from src.parser import normalize_components

    normalized = normalize_components(parsed_result.get("parsed", {}))
    validation_result = validate_address(normalized)

    # Format address
    formatted_result = create_formatted_address_result(address, parsed_result, validation_result)

    return formatted_result


def write_output(
    results: List[Dict[str, Any]],
    output_path: str,
    format: str,
    logger,
    original_df: Optional[pd.DataFrame] = None,
    csv_options: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Write results to output file in specified format.

    Args:
        results: List of processing results
        output_path: Path to output file
        format: Output format (csv, json, excel)
        logger: Logger instance
        original_df: Original DataFrame to preserve columns from (optional)
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:  # Only create if there's a directory component
        ensure_directory_exists(output_dir)

    if format == "csv":
        write_csv_output(results, output_path, logger, original_df, csv_options or {})
    elif format == "json":
        write_json_output(
            results,
            output_path,
            logger,
            original_df,
            encoding=(csv_options or {}).get("encoding", "utf-8"),
        )
    elif format == "excel":
        write_excel_output(
            results,
            output_path,
            logger,
            original_df,
            encoding=(csv_options or {}).get("encoding", "utf-8"),
        )


def _create_column_mapping(original_columns: List[str], parsed_df: pd.DataFrame) -> Dict[str, str]:
    """
    Create a mapping from original column names to cleaned column names.

    Maps columns like 'Street' -> 'cleaned_street_name', 'City' -> 'cleaned_city', etc.
    Intelligently detects column purposes based on common naming patterns.

    Args:
        original_columns: List of original column names from input
        parsed_df: DataFrame with cleaned_* columns

    Returns:
        Dictionary mapping original column name to cleaned column name
    """
    mapping = {}

    # Available cleaned columns
    available_cleaned = set(parsed_df.columns)

    # Check if we have separate address component columns
    has_separate_components = (
        any("city" in col.lower() for col in original_columns)
        or any("state" in col.lower() and "estate" not in col.lower() for col in original_columns)
        or any(word in col.lower() for col in original_columns for word in ["zip", "postal"])
    )

    for col in original_columns:
        col_lower = col.lower()

        # Full address column (contains full address string)
        if any(word in col_lower for word in ["full_address", "fulladdress", "complete_address"]):
            if "cleaned_formatted_address" in available_cleaned:
                mapping[col] = "cleaned_formatted_address"
                continue

        # Generic address column (typically street address)
        if col_lower in ["address", "addr", "street_address", "streetaddress", "mailing_address"]:
            # If separate components exist, use street-only address
            if has_separate_components and "cleaned_street_address_only" in available_cleaned:
                mapping[col] = "cleaned_street_address_only"
            elif "cleaned_formatted_address" in available_cleaned:
                mapping[col] = "cleaned_formatted_address"
            continue

        # City column
        if "city" in col_lower:
            if "cleaned_city" in available_cleaned:
                mapping[col] = "cleaned_city"
            continue

        # State column
        if "state" in col_lower and "estate" not in col_lower:
            if "cleaned_state" in available_cleaned:
                mapping[col] = "cleaned_state"
            continue

        # ZIP/Postal code column
        if any(word in col_lower for word in ["zip", "postal", "postcode", "zipcode"]):
            if "cleaned_zip_code" in available_cleaned:
                mapping[col] = "cleaned_zip_code"
            continue

        # Street/Street Address column
        if (
            any(word in col_lower for word in ["street", "street_address"])
            and "city" not in col_lower
        ):
            # Combine street components into formatted street
            if "cleaned_street_number" in available_cleaned:
                # We'll need to create a combined street field
                # For now, use formatted address
                mapping[col] = "cleaned_formatted_address"
            continue

        # PO Box column
        if any(word in col_lower for word in ["po_box", "pobox", "p.o.box", "p.o. box"]):
            if "cleaned_po_box" in available_cleaned:
                mapping[col] = "cleaned_po_box"
            continue

        # Unit/Apt/Suite column
        if any(word in col_lower for word in ["unit", "apt", "apartment", "suite", "ste"]):
            if "cleaned_unit" in available_cleaned:
                mapping[col] = "cleaned_unit"
            continue

    return mapping


def write_csv_output(
    results: List[Dict[str, Any]],
    output_path: str,
    logger,
    original_df: Optional[pd.DataFrame] = None,
    csv_options: Optional[Dict[str, Any]] = None,
) -> None:
    """Write results to CSV file, optionally preserving original columns."""
    import os

    csv_options = csv_options or {}
    delimiter = csv_options.get("delimiter", ",")
    encoding = csv_options.get("encoding", "utf-8")
    quote_mode = csv_options.get("quote", "minimal")
    newline_opt = csv_options.get("newline", "system")
    excel_friendly = bool(csv_options.get("excel_friendly", False))
    prune_empty_cleaned = bool(csv_options.get("prune_empty_cleaned", False))
    update_in_place = bool(csv_options.get("update_in_place", False))

    # Excel-friendly preset overrides
    if excel_friendly:
        encoding = "utf-8-sig"
        newline_opt = "crlf"
        quote_mode = "all"

    # Map quote option to csv constants
    if quote_mode == "all":
        quoting_mode = csv.QUOTE_ALL
    elif quote_mode == "nonnumeric":
        quoting_mode = csv.QUOTE_NONNUMERIC
    elif quote_mode == "none":
        quoting_mode = csv.QUOTE_NONE
    else:
        quoting_mode = csv.QUOTE_MINIMAL

    # Determine line terminator
    if newline_opt == "lf":
        line_ending = "\n"
    elif newline_opt == "crlf":
        line_ending = "\r\n"
    else:
        line_ending = os.linesep

    # QUOTE_NONE requires an escapechar
    extra_to_csv = {}
    if quoting_mode == csv.QUOTE_NONE:
        extra_to_csv["escapechar"] = "\\"

    logger.info(
        f"Writing CSV output to: {output_path} "
        f"(delimiter='{delimiter}', encoding='{encoding}', "
        f"quoting='{quote_mode}', newline='{newline_opt}')"
    )

    # Prepare parsed address data
    parsed_data = []
    for result in results:
        row = {
            "cleaned_original_address": result["original"],
            "cleaned_street_number": result["parsed"].get("street_number", ""),
            "cleaned_street_name": result["parsed"].get("street_name", ""),
            "cleaned_street_type": result["parsed"].get("street_type", ""),
            "cleaned_city": result["parsed"].get("city", ""),
            "cleaned_state": result["parsed"].get("state", ""),
            "cleaned_zip_code": result["parsed"].get("zip_code", ""),
            "cleaned_unit": result["parsed"].get("unit", ""),
            "cleaned_po_box": result["parsed"].get("po_box", ""),
            "cleaned_formatted_address": result["single_line"],
            "cleaned_confidence_score": result["confidence"],
            "cleaned_validation_status": "Valid" if result["valid"] else "Invalid",
            "cleaned_issues": "; ".join(result["issues"]) if result["issues"] else "",
            "cleaned_address_type": result["address_type"],
        }
        parsed_data.append(row)

    parsed_df = pd.DataFrame(parsed_data)

    # Handle update-in-place mode: mirror input structure with cleaned values
    if update_in_place and original_df is not None and len(original_df) == len(parsed_df):
        logger.info("Update-in-place mode: mirroring input structure with cleaned values")
        output_df = original_df.copy()

        # Check if we have separate City/State/Zip columns
        has_city_col = any("city" in col.lower() for col in original_df.columns)
        has_state_col = any(
            "state" in col.lower() and "estate" not in col.lower() for col in original_df.columns
        )
        has_zip_col = any(
            word in col.lower() for col in original_df.columns for word in ["zip", "postal"]
        )

        # Create combined street address if needed (for separate column formats)
        if has_city_col or has_state_col or has_zip_col:
            street_parts = []
            for idx in range(len(parsed_df)):
                # Check for PO Box first
                po_box = parsed_df["cleaned_po_box"].iloc[idx]
                if po_box:
                    # Use PO Box as the address (ensure "PO BOX" prefix)
                    po_box_str = str(po_box)
                    if not po_box_str.upper().startswith("PO"):
                        street_addr = f"PO BOX {po_box_str}"
                    else:
                        street_addr = po_box_str
                else:
                    # Build street address: number + name + type (space-separated)
                    street_components = []
                    if parsed_df["cleaned_street_number"].iloc[idx]:
                        street_components.append(str(parsed_df["cleaned_street_number"].iloc[idx]))
                    if parsed_df["cleaned_street_name"].iloc[idx]:
                        street_components.append(str(parsed_df["cleaned_street_name"].iloc[idx]))
                    if parsed_df["cleaned_street_type"].iloc[idx]:
                        street_components.append(str(parsed_df["cleaned_street_type"].iloc[idx]))
                    street_addr = " ".join(street_components)

                # Add unit/apt if present (comma-separated)
                unit = parsed_df["cleaned_unit"].iloc[idx]
                if unit and street_addr:
                    street_addr = f"{street_addr}, {unit}"
                elif unit:
                    street_addr = str(unit)

                street_parts.append(street_addr if street_addr else "")
            parsed_df["cleaned_street_address_only"] = street_parts
            logger.debug("Created cleaned_street_address_only column for separate components")

        # Map cleaned components to original columns
        column_mapping = _create_column_mapping(original_df.columns, parsed_df)

        # Update each mapped column with cleaned data, but only if parsing was successful
        for orig_col, cleaned_col in column_mapping.items():
            if cleaned_col in parsed_df.columns:
                orig_col_lower = orig_col.lower()

                # For each row, only update if parsing was reasonably successful
                for idx in range(len(output_df)):
                    confidence = parsed_df["cleaned_confidence_score"].iloc[idx]
                    is_valid = parsed_df["cleaned_validation_status"].iloc[idx] == "Valid"
                    cleaned_value = parsed_df[cleaned_col].iloc[idx]
                    original_value = output_df.loc[idx, orig_col]

                    # Sanity checks for specific column types
                    should_update = False

                    if pd.notna(cleaned_value) and str(cleaned_value).strip() != "":
                        cleaned_str = str(cleaned_value)

                        # For State columns: reject if contains comma or numbers
                        if "state" in orig_col_lower:
                            if "," in cleaned_str or any(c.isdigit() for c in cleaned_str):
                                logger.debug(
                                    f"Row {idx}: Keeping original State '{original_value}' "
                                    f"(cleaned value '{cleaned_str}' looks invalid)"
                                )
                                continue

                        # For Zip columns: reject if it doesn't look like a ZIP
                        if any(word in orig_col_lower for word in ["zip", "postal"]):
                            # ZIP should be mostly digits
                            if not any(c.isdigit() for c in cleaned_str):
                                logger.debug(
                                    f"Row {idx}: Keeping original Zip '{original_value}' "
                                    f"(cleaned value '{cleaned_str}' has no digits)"
                                )
                                continue

                        # Update if valid OR high confidence
                        if is_valid or confidence >= 70:
                            should_update = True
                        # For invalid addresses, only update if confidence is very high (formatting fixes)
                        elif not is_valid and confidence >= 85:
                            should_update = True
                        else:
                            logger.debug(
                                f"Row {idx}: Keeping original '{orig_col}' = '{original_value}' "
                                f"(cleaned '{cleaned_str}' confidence: {confidence}, valid: {is_valid})"
                            )

                    if should_update:
                        output_df.loc[idx, orig_col] = cleaned_value

                logger.debug(f"Mapped '{orig_col}' <- '{cleaned_col}'")

        logger.info(
            f"Updated {len(column_mapping)} columns in-place; "
            f"output has {len(output_df.columns)} columns (same as input)"
        )

    # Merge with original DataFrame if provided (standard preserve mode)
    elif original_df is not None and len(original_df) == len(parsed_df):
        output_df = pd.concat(
            [original_df.reset_index(drop=True), parsed_df.reset_index(drop=True)], axis=1
        )
        logger.info(f"Preserved {len(original_df.columns)} original columns in output")
    else:
        # Use cleaned_ prefix removal for backward compatibility when not preserving
        output_df = parsed_df.copy()
        output_df.columns = [col.replace("cleaned_", "") for col in output_df.columns]

    if original_df is not None and prune_empty_cleaned:
        cleaned_cols = [col for col in output_df.columns if col.startswith("cleaned_")]
        non_empty_cleaned = []
        for col in cleaned_cols:
            if output_df[col].notna().any() and (output_df[col] != "").any():
                non_empty_cleaned.append(col)
        cols_to_keep = list(original_df.columns) + non_empty_cleaned
        for col in output_df.columns:
            if not col.startswith("cleaned_") and col not in cols_to_keep:
                cols_to_keep.append(col)
        output_df = output_df[cols_to_keep]
        if len(cleaned_cols) != len(non_empty_cleaned):
            logger.info(
                f"Removed {len(cleaned_cols) - len(non_empty_cleaned)} "
                f"empty cleaned columns for cleaner output"
            )

    # Write to CSV with standard formatting
    # Replace NaN/None with empty string
    output_df = output_df.fillna("")
    output_df.to_csv(
        output_path,
        index=False,
        sep=delimiter,
        quoting=quoting_mode,
        lineterminator=line_ending,
        encoding=encoding,
        **extra_to_csv,
    )


def write_json_output(
    results: List[Dict[str, Any]],
    output_path: str,
    logger,
    original_df: Optional[pd.DataFrame] = None,
    encoding: str = "utf-8",
) -> None:
    """Write results to JSON file, optionally including original data."""
    logger.info(f"Writing JSON output to: {output_path}")

    output_data = {
        "results": results,
        "summary": calculate_processing_stats(results),
        "timestamp": pd.Timestamp.now().isoformat(),
    }

    # Include original data if preserving columns
    if original_df is not None:
        output_data["original_data"] = original_df.to_dict("records")
        logger.info(f"Included {len(original_df.columns)} original columns in JSON output")

    with open(output_path, "w", encoding=encoding) as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)


def write_excel_output(
    results: List[Dict[str, Any]],
    output_path: str,
    logger,
    original_df: Optional[pd.DataFrame] = None,
    encoding: str = "utf-8",
) -> None:
    """Write results to Excel file, optionally preserving original columns."""
    logger.info(f"Writing Excel output to: {output_path}")

    # Prepare parsed address data
    parsed_data = []
    for result in results:
        row = {
            "Cleaned Original Address": result["original"],
            "Cleaned Street Number": result["parsed"].get("street_number", ""),
            "Cleaned Street Name": result["parsed"].get("street_name", ""),
            "Cleaned Street Type": result["parsed"].get("street_type", ""),
            "Cleaned City": result["parsed"].get("city", ""),
            "Cleaned State": result["parsed"].get("state", ""),
            "Cleaned ZIP Code": result["parsed"].get("zip_code", ""),
            "Cleaned Unit": result["parsed"].get("unit", ""),
            "Cleaned PO Box": result["parsed"].get("po_box", ""),
            "Cleaned Formatted Address": result["single_line"],
            "Cleaned Confidence Score": result["confidence"],
            "Cleaned Validation Status": "Valid" if result["valid"] else "Invalid",
            "Cleaned Issues": "; ".join(result["issues"]) if result["issues"] else "",
            "Cleaned Address Type": result["address_type"],
        }
        parsed_data.append(row)

    parsed_df = pd.DataFrame(parsed_data)

    # Merge with original DataFrame if provided
    if original_df is not None and len(original_df) == len(parsed_df):
        # Convert original column names to proper case for Excel
        original_df_formatted = original_df.copy()
        output_df = pd.concat(
            [original_df_formatted.reset_index(drop=True), parsed_df.reset_index(drop=True)], axis=1
        )
        logger.info(f"Preserved {len(original_df.columns)} original columns in output")
    else:
        # Remove cleaned_ prefix for backward compatibility
        output_df = parsed_df.copy()
        output_df.columns = [col.replace("Cleaned ", "") for col in output_df.columns]

    # Write to Excel with formatting
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        output_df.to_excel(writer, sheet_name="Addresses", index=False)

        # Add summary sheet
        stats = calculate_processing_stats(results)
        summary_data = {
            "Metric": [
                "Total Processed",
                "Successful",
                "Failed",
                "Success Rate (%)",
                "Average Confidence",
            ],
            "Value": [
                stats["total_processed"],
                stats["successful"],
                stats["failed"],
                stats["success_rate"],
                stats["average_confidence"],
            ],
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)


def write_validation_report(results: List[Dict[str, Any]], report_path: str, logger) -> None:
    """Write validation report to file."""
    logger.info(f"Writing validation report to: {report_path}")

    stats = calculate_processing_stats(results)

    report_content = f"""Address Cleanser Validation Report
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY STATISTICS
==================
Total Addresses Processed: {stats['total_processed']}
Successful Validations: {stats['successful']}
Failed Validations: {stats['failed']}
Success Rate: {stats['success_rate']}%
Average Confidence Score: {stats['average_confidence']}%

DETAILED RESULTS
===============
"""

    # Add detailed results
    for i, result in enumerate(results, 1):
        report_content += f"\n{i}. {result['original']}\n"
        report_content += f"   Formatted: {result['single_line']}\n"
        report_content += f"   Valid: {'Yes' if result['valid'] else 'No'}\n"
        report_content += f"   Confidence: {result['confidence']:.1f}%\n"
        if result["issues"]:
            report_content += f"   Issues: {', '.join(result['issues'])}\n"

    # Write report
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)


if __name__ == "__main__":
    try:
        # Ensure stderr is normal for logging (restore if it was suppressed)
        if hasattr(sys, "frozen") and sys.frozen and hasattr(sys, "_original_stderr"):
            sys.stderr = sys._original_stderr

        # Run the CLI
        cli()

        # After successful execution, enter cleanup mode
        # This prevents PyInstaller bootloader from printing errors
        if hasattr(sys, "frozen") and sys.frozen:
            sys._cleanup_mode = True
            if hasattr(sys, "_null_stderr"):
                sys.stderr = sys._null_stderr
            else:
                sys.stderr = io.StringIO()

    except (FileNotFoundError, OSError) as e:
        # Suppress PyInstaller cleanup errors
        if hasattr(sys, "frozen") and sys.frozen:
            if "base_library.zip" in str(e) or "_MEI" in str(e):
                # Processing already completed successfully
                if hasattr(sys, "_null_stderr"):
                    sys.stderr = sys._null_stderr
                else:
                    sys.stderr = io.StringIO()
                sys.exit(0)
        # Re-raise other errors
        raise
    except SystemExit as e:
        # Suppress stderr before exit to prevent bootloader error message
        if hasattr(sys, "frozen") and sys.frozen:
            if hasattr(sys, "_null_stderr"):
                sys.stderr = sys._null_stderr
            else:
                sys.stderr = io.StringIO()
        raise
    except Exception as e:
        # Suppress any other cleanup-related errors in PyInstaller
        if hasattr(sys, "frozen") and sys.frozen:
            # Suppress stderr and exit cleanly
            if hasattr(sys, "_null_stderr"):
                sys.stderr = sys._null_stderr
            else:
                sys.stderr = io.StringIO()
            sys.exit(0)
        raise
