"""
Test module for CLI functionality.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pandas as pd
import pytest


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_single_command_json_output(self):
        """Test single address command with JSON output."""
        result = subprocess.run(
            [
                "python3",
                "cli.py",
                "single",
                "--single",
                "123 Main Street, Austin, TX 78701",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )

        assert result.returncode == 0
        # stderr contains logging output, which is expected
        assert "Address Cleanser started" in result.stderr

        # Parse JSON output
        output = json.loads(result.stdout)
        assert output["original"] == "123 Main Street, Austin, TX 78701"
        assert output["confidence"] > 0
        assert output["valid"] is True
        assert "MAIN ST" in output["single_line"]

    def test_single_command_csv_output(self):
        """Test single address command with CSV output."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_file = f.name

        try:
            result = subprocess.run(
                [
                    "python3",
                    "cli.py",
                    "single",
                    "--single",
                    "123 Main Street, Austin, TX 78701",
                    "--format",
                    "csv",
                    "--output",
                    temp_file,
                ],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )

            assert result.returncode == 0

            # Check CSV output
            df = pd.read_csv(temp_file)
            assert len(df) == 1
            assert df.iloc[0]["original_address"] == "123 Main Street, Austin, TX 78701"
            assert df.iloc[0]["confidence_score"] > 0
            assert df.iloc[0]["validation_status"] == "Valid"

        finally:
            os.unlink(temp_file)

    def test_batch_command_csv_output(self):
        """Test batch command with CSV output."""
        # Create test input file with properly quoted addresses
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("address\n")
            f.write('"123 Main Street, Austin, TX 78701"\n')
            f.write('"456 Oak Avenue, Dallas, TX 75201"\n')
            input_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_file = f.name

        try:
            result = subprocess.run(
                [
                    "python3",
                    "cli.py",
                    "batch",
                    "--input",
                    input_file,
                    "--output",
                    output_file,
                    "--format",
                    "csv",
                ],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )

            assert result.returncode == 0

            # Check CSV output
            df = pd.read_csv(output_file)
            assert len(df) == 2
            assert df.iloc[0]["original_address"] == "123 Main Street, Austin, TX 78701"
            assert df.iloc[1]["original_address"] == "456 Oak Avenue, Dallas, TX 75201"

        finally:
            os.unlink(input_file)
            os.unlink(output_file)

    def test_batch_command_json_output(self):
        """Test batch command with JSON output."""
        # Create test input file with properly quoted addresses
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("address\n")
            f.write('"123 Main Street, Austin, TX 78701"\n')
            f.write('"456 Oak Avenue, Dallas, TX 75201"\n')
            input_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            result = subprocess.run(
                [
                    "python3",
                    "cli.py",
                    "batch",
                    "--input",
                    input_file,
                    "--output",
                    output_file,
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )

            assert result.returncode == 0

            # Check JSON output
            with open(output_file, "r") as f:
                output = json.load(f)

            assert "results" in output
            assert "summary" in output
            assert len(output["results"]) == 2
            assert output["summary"]["total_processed"] == 2

        finally:
            os.unlink(input_file)
            os.unlink(output_file)

    def test_batch_command_with_report(self):
        """Test batch command with validation report."""
        # Create test input file with properly quoted addresses
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("address\n")
            f.write('"123 Main Street, Austin, TX 78701"\n')
            f.write('"Invalid Address"\n')
            input_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            report_file = f.name

        try:
            result = subprocess.run(
                [
                    "python3",
                    "cli.py",
                    "batch",
                    "--input",
                    input_file,
                    "--output",
                    output_file,
                    "--format",
                    "csv",
                    "--report",
                    report_file,
                ],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )

            assert result.returncode == 0

            # Check report file exists and has content
            assert os.path.exists(report_file)
            with open(report_file, "r") as f:
                report_content = f.read()

            assert "Address Cleanser Validation Report" in report_content
            assert "SUMMARY STATISTICS" in report_content

        finally:
            os.unlink(input_file)
            os.unlink(output_file)
            os.unlink(report_file)

    def test_custom_address_column(self):
        """Test batch command with custom address column name."""
        # Create test input file with custom column name and properly quoted addresses
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("full_address\n")
            f.write('"123 Main Street, Austin, TX 78701"\n')
            input_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_file = f.name

        try:
            result = subprocess.run(
                [
                    "python3",
                    "cli.py",
                    "batch",
                    "--input",
                    input_file,
                    "--output",
                    output_file,
                    "--address-column",
                    "full_address",
                ],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )

            assert result.returncode == 0

            # Check CSV output
            df = pd.read_csv(output_file)
            assert len(df) == 1
            assert df.iloc[0]["original_address"] == "123 Main Street, Austin, TX 78701"

        finally:
            os.unlink(input_file)
            os.unlink(output_file)

    def test_error_handling_invalid_file(self):
        """Test error handling for invalid input file."""
        result = subprocess.run(
            ["python3", "cli.py", "batch", "--input", "nonexistent.csv", "--output", "output.csv"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )

        assert result.returncode == 1
        assert "Input file does not exist" in result.stderr

    def test_error_handling_invalid_format(self):
        """Test error handling for invalid file format."""
        # Create non-CSV file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is not a CSV file\n")
            input_file = f.name

        try:
            result = subprocess.run(
                ["python3", "cli.py", "batch", "--input", input_file, "--output", "output.csv"],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )

            assert result.returncode == 1
            assert "Invalid input file format" in result.stderr

        finally:
            os.unlink(input_file)

    def test_log_level_configuration(self):
        """Test log level configuration."""
        result = subprocess.run(
            [
                "python3",
                "cli.py",
                "--log-level",
                "DEBUG",
                "single",
                "--single",
                "123 Main Street, Austin, TX 78701",
            ],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )

        assert result.returncode == 0
        assert "DEBUG" in result.stderr

    def test_chunk_size_configuration(self):
        """Test chunk size configuration."""
        # Create test input file with multiple addresses
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("address\n")
            for i in range(5):
                f.write(f"{i+1} Test Street, Austin, TX 78701\n")
            input_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_file = f.name

        try:
            result = subprocess.run(
                [
                    "python3",
                    "cli.py",
                    "batch",
                    "--input",
                    input_file,
                    "--output",
                    output_file,
                    "--chunk-size",
                    "2",
                ],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )

            assert result.returncode == 0

            # Check CSV output
            df = pd.read_csv(output_file)
            assert len(df) == 5

        finally:
            os.unlink(input_file)
            os.unlink(output_file)
