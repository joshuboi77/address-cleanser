"""
Command-line interface for the Address Cleanser tool.

This module provides a CLI interface using Click for processing addresses
in CSV, JSON, and Excel formats.
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional

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
        results, original_df = process_csv_file(
            input,
            address_column,
            address_columns,
            preserve_columns,
            auto_combine,
            chunk_size,
            logger,
        )

        # Write output
        write_output(results, output, format, logger, original_df if preserve_columns else None)

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
) -> tuple[List[Dict[str, Any]], Optional[pd.DataFrame]]:
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

    # Get addresses
    addresses = df[actual_address_column].dropna().tolist()
    logger.info(f"Found {len(addresses)} addresses to process")

    # Process addresses in chunks
    results = []
    for i in tqdm(range(0, len(addresses), chunk_size), desc="Processing addresses"):
        chunk = addresses[i : i + chunk_size]
        chunk_results = []

        for address in chunk:
            try:
                result = process_single_address(address, logger)
                chunk_results.append(result)
            except Exception as e:
                logger.warning(f"Error processing address '{address}': {str(e)}")
                chunk_results.append(
                    {
                        "original": address,
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
        write_csv_output(results, output_path, logger, original_df)
    elif format == "json":
        write_json_output(results, output_path, logger, original_df)
    elif format == "excel":
        write_excel_output(results, output_path, logger, original_df)


def write_csv_output(
    results: List[Dict[str, Any]],
    output_path: str,
    logger,
    original_df: Optional[pd.DataFrame] = None,
) -> None:
    """Write results to CSV file, optionally preserving original columns."""
    logger.info(f"Writing CSV output to: {output_path}")

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

    # Merge with original DataFrame if provided
    if original_df is not None and len(original_df) == len(parsed_df):
        output_df = pd.concat(
            [original_df.reset_index(drop=True), parsed_df.reset_index(drop=True)], axis=1
        )
        logger.info(f"Preserved {len(original_df.columns)} original columns in output")
    else:
        # Use cleaned_ prefix removal for backward compatibility when not preserving
        output_df = parsed_df.copy()
        output_df.columns = [col.replace("cleaned_", "") for col in output_df.columns]

    # Write to CSV
    output_df.to_csv(output_path, index=False)


def write_json_output(
    results: List[Dict[str, Any]],
    output_path: str,
    logger,
    original_df: Optional[pd.DataFrame] = None,
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

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)


def write_excel_output(
    results: List[Dict[str, Any]],
    output_path: str,
    logger,
    original_df: Optional[pd.DataFrame] = None,
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
    cli()
