"""
Command-line interface for the Address Cleanser tool.

This module provides a CLI interface using Click for processing addresses
in CSV, JSON, and Excel formats.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import pandas as pd
from tqdm import tqdm

from src.formatter import create_formatted_address_result
from src.parser import handle_edge_cases, parse_address
from src.utils import (
    calculate_processing_stats,
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
    "--address-column", "-c", default="address", help="Name of the address column in input CSV"
)
@click.option("--report", "-r", help="Validation report file path (optional)")
@click.option("--chunk-size", default=1000, help="Process addresses in chunks of this size")
@click.pass_context
def batch(ctx, input, output, format, address_column, report, chunk_size):
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
        results = process_csv_file(input, address_column, chunk_size, logger)

        # Write output
        write_output(results, output, format, logger)

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
    input_file: str, address_column: str, chunk_size: int, logger
) -> List[Dict[str, Any]]:
    """
    Process addresses from a CSV file.

    Args:
        input_file: Path to input CSV file
        address_column: Name of the address column
        chunk_size: Number of addresses to process at once

    Returns:
        List of processing results
    """
    logger.info(f"Reading CSV file: {input_file}")

    # Read CSV file
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        logger.error(f"Error reading CSV file: {str(e)}")
        raise

    # Check if address column exists
    if address_column not in df.columns:
        logger.error(
            f"Address column '{address_column}' not found in CSV. Available columns: {list(df.columns)}"
        )
        raise ValueError(f"Address column '{address_column}' not found")

    # Get addresses
    addresses = df[address_column].dropna().tolist()
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

    return results


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


def write_output(results: List[Dict[str, Any]], output_path: str, format: str, logger) -> None:
    """
    Write results to output file in specified format.

    Args:
        results: List of processing results
        output_path: Path to output file
        format: Output format (csv, json, excel)
        logger: Logger instance
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:  # Only create if there's a directory component
        ensure_directory_exists(output_dir)

    if format == "csv":
        write_csv_output(results, output_path, logger)
    elif format == "json":
        write_json_output(results, output_path, logger)
    elif format == "excel":
        write_excel_output(results, output_path, logger)


def write_csv_output(results: List[Dict[str, Any]], output_path: str, logger) -> None:
    """Write results to CSV file."""
    logger.info(f"Writing CSV output to: {output_path}")

    # Prepare data for CSV
    csv_data = []
    for result in results:
        row = {
            "original_address": result["original"],
            "street_number": result["parsed"].get("street_number", ""),
            "street_name": result["parsed"].get("street_name", ""),
            "street_type": result["parsed"].get("street_type", ""),
            "city": result["parsed"].get("city", ""),
            "state": result["parsed"].get("state", ""),
            "zip_code": result["parsed"].get("zip_code", ""),
            "unit": result["parsed"].get("unit", ""),
            "po_box": result["parsed"].get("po_box", ""),
            "formatted_address": result["single_line"],
            "confidence_score": result["confidence"],
            "validation_status": "Valid" if result["valid"] else "Invalid",
            "issues": "; ".join(result["issues"]) if result["issues"] else "",
            "address_type": result["address_type"],
        }
        csv_data.append(row)

    # Write to CSV
    df = pd.DataFrame(csv_data)
    df.to_csv(output_path, index=False)


def write_json_output(results: List[Dict[str, Any]], output_path: str, logger) -> None:
    """Write results to JSON file."""
    logger.info(f"Writing JSON output to: {output_path}")

    output_data = {
        "results": results,
        "summary": calculate_processing_stats(results),
        "timestamp": pd.Timestamp.now().isoformat(),
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)


def write_excel_output(results: List[Dict[str, Any]], output_path: str, logger) -> None:
    """Write results to Excel file."""
    logger.info(f"Writing Excel output to: {output_path}")

    # Prepare data for Excel
    excel_data = []
    for result in results:
        row = {
            "Original Address": result["original"],
            "Street Number": result["parsed"].get("street_number", ""),
            "Street Name": result["parsed"].get("street_name", ""),
            "Street Type": result["parsed"].get("street_type", ""),
            "City": result["parsed"].get("city", ""),
            "State": result["parsed"].get("state", ""),
            "ZIP Code": result["parsed"].get("zip_code", ""),
            "Unit": result["parsed"].get("unit", ""),
            "PO Box": result["parsed"].get("po_box", ""),
            "Formatted Address": result["single_line"],
            "Confidence Score": result["confidence"],
            "Validation Status": "Valid" if result["valid"] else "Invalid",
            "Issues": "; ".join(result["issues"]) if result["issues"] else "",
            "Address Type": result["address_type"],
        }
        excel_data.append(row)

    # Write to Excel with formatting
    df = pd.DataFrame(excel_data)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Addresses", index=False)

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
