# Address Cleanser

A Python CLI tool for parsing, validating, and formatting US addresses according to USPS Publication 28 standards.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI](https://github.com/joshuboi77/address-cleanser/workflows/CI/badge.svg)](https://github.com/joshuboi77/address-cleanser/actions)

## Features

- **Address Parsing**: Uses the `usaddress` library for NLP-based address parsing
- **Offline Validation**: Validates ZIP codes, state abbreviations, and address completeness
- **USPS Formatting**: Formats addresses according to USPS Publication 28 standards
- **Multiple Output Formats**: Supports CSV, JSON, and Excel output formats (input: CSV only)
- **Batch Processing**: Process large CSV files with progress tracking
- **Single Address Processing**: Process individual addresses from command line
- **Column Preservation**: Preserve original CSV columns while adding cleaned address fields
- **Flexible Input**: Accept addresses in a single column OR auto-detect and combine separate columns

## Quick Start

Get up and running in 3 steps:

1. **Install dependencies:**
   ```bash
   bash install.sh
   ```

2. **Test with sample data:**
   ```bash
   # If installed: address-cleanser batch --input out/sample_input.csv --output test_results.csv --format csv
   # If from source: python3 cli.py batch --input out/sample_input.csv --output test_results.csv --format csv
   ```

3. **Process a single address:**
   ```bash
   # If installed: address-cleanser single --single "123 Main Street, Austin, TX 78701"
   # If from source: python3 cli.py single --single "123 Main Street, Austin, TX 78701"
   ```

**Expected Output Preview:**
```
Original: 123 Main Street, Austin, TX 78701
Formatted: 123 MAIN ST, AUSTIN, TX, 78701
Valid: Yes
Confidence: 90.0%
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- ~50MB disk space for dependencies

### Install Dependencies

**Recommended (automatic):**
```bash
bash install.sh
```

**Manual installation:**
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install usaddress pandas openpyxl click tqdm psutil
```

## Usage

### Command Line Interface

**Command Invocation:**
- If installed as a package or via Homebrew: use `address-cleanser`
- If running from source: use `python cli.py` or `python3 cli.py`

**Command Structure:**
```bash
address-cleanser [OPTIONS] COMMAND [ARGS]...
```

The tool provides two main commands:
- `batch` - Process addresses from a CSV file
- `single` - Process a single address

#### Batch Processing

Process addresses from a CSV file (CSV input only; output can be CSV, JSON, or Excel):

```bash
address-cleanser batch --input addresses.csv --output cleaned_addresses.csv --format csv
```

**Options:**
- `--input, -i`: Input CSV file path (required) - **Note: Only CSV files are supported as input**
- `--output, -o`: Output file path (required)
- `--format, -f`: Output format - csv, json, or excel (default: csv)
- `--address-column, -c`: Name of the address column in CSV (auto-detected if not specified)
- `--address-columns, -C`: Comma-separated list of columns to combine (e.g., `"Address,City,State,Zip"`)
- `--preserve-columns, -p`: Preserve all original CSV columns in output
- `--auto-combine, -a`: Auto-detect and combine separate address columns
- `--report, -r`: Generate validation report file (optional)
- `--chunk-size`: Process addresses in chunks of this size (default: 1000)

**Examples:**

```bash
# Process CSV file and output to CSV
address-cleanser batch --input addresses.csv --output cleaned.csv --format csv

# Process CSV file and output to Excel with validation report
address-cleanser batch --input addresses.csv --output results.xlsx --format excel --report validation.txt

# Process with custom address column name (case-sensitive)
address-cleanser batch --input data.csv --output output.csv --address-column "Address"

# Example: If your CSV has "full_address" instead of "address"
address-cleanser batch --input data.csv --output output.csv --address-column "full_address"

# Process CSV with separate address columns and preserve original columns
address-cleanser batch --input data.csv --output cleaned.csv --preserve-columns --auto-combine

# Explicitly specify which columns to combine
address-cleanser batch --input data.csv --output cleaned.csv --preserve-columns --address-columns "Address,City,State,Zip"

# Preserve columns and output to Excel
address-cleanser batch --input client_data.csv --output cleaned.xlsx --format excel --preserve-columns --auto-combine
```

#### Single Address Processing

Process a single address:

```bash
address-cleanser single --single "123 Main Street, Austin, TX 78701" --format json
```

**Options:**
- `--single, -s`: Single address to process (required)
- `--format, -f`: Output format - csv, json, or excel (default: json)
- `--output, -o`: Output file path (optional, prints to console if not specified)

**Examples:**

```bash
# Process single address and print to console
address-cleanser single --single "123 Main Street, Austin, TX 78701"

# Process single address and save to file
address-cleanser single --single "PO Box 123, Austin, TX 78701" --output result.json --format json
```

### Input Format

**Input Requirements:** The CLI accepts **CSV files only** as input. Excel files (.xlsx) are not supported for input, but you can output to Excel format. To process an Excel file, first export it to CSV format.

**Address Column Formats:** The tool supports two input formats:

1. **Single Combined Column** (default): One column with complete address string
   ```csv
   address
   123 Main Street, Austin, TX 78701
   ```

2. **Separate Columns**: Address components in multiple columns
   ```csv
   Address,City,State,Zip
   123 Main Street,Austin,TX,78701
   ```
   Use `--auto-combine` to auto-detect and combine, or `--address-columns "Address,City,State,Zip"` to specify manually.

**Column Detection:**
- By default, looks for a column named `address` (case-sensitive, lowercase)
- Use `--address-column` to specify a different single column name
- Use `--auto-combine` to automatically detect and combine separate address columns
- Use `--address-columns` to explicitly specify which columns to combine (comma-separated)

**Column Preservation:**
- Use `--preserve-columns` to keep all original CSV columns in the output
- Original columns appear first, followed by `cleaned_*` columns with parsed/cleaned data
- Perfect for maintaining client data structures while adding cleaned address fields

**Example CSV Formats:**

*Single combined column (preferred):*
```csv
address
123 Main Street, Austin, TX 78701
456 Oak Avenue, Dallas, TX 75201
```

*Separate columns (also supported):*
```csv
Name,Address,City,State,Zip,Phone
John Smith,123 Main St,Austin,TX,78701,555-0101
```

### Output Formats

#### CSV Output

**Standard Output** (without `--preserve-columns`):
The CSV output includes the following columns:
- `original_address`: Original input address
- `street_number`: Parsed street number
- `street_name`: Parsed street name
- `street_type`: Parsed street type (ST, AVE, etc.)
- `city`: Parsed city name
- `state`: Parsed state abbreviation
- `zip_code`: Parsed ZIP code
- `unit`: Unit/apartment information
- `po_box`: PO Box number
- `formatted_address`: USPS-formatted single-line address
- `confidence_score`: Parsing confidence (0-100)
- `validation_status`: Valid or Invalid
- `issues`: List of validation issues
- `address_type`: Type of address (Street Address, PO Box, etc.)

**With Column Preservation** (using `--preserve-columns`):
- **All original columns** are preserved in their original order
- **New `cleaned_*` columns** are appended:
  - `cleaned_original_address`
  - `cleaned_street_number`
  - `cleaned_street_name`
  - `cleaned_street_type`
  - `cleaned_city`
  - `cleaned_state`
  - `cleaned_zip_code`
  - `cleaned_unit`
  - `cleaned_po_box`
  - `cleaned_formatted_address`
  - `cleaned_confidence_score`
  - `cleaned_validation_status`
  - `cleaned_issues`
  - `cleaned_address_type`

This allows you to maintain your original data structure while adding cleaned address fields.

#### JSON Output

**Standard Output** (without `--preserve-columns`):
The JSON output includes:
- `results`: Array of processing results
- `summary`: Processing statistics
- `timestamp`: Processing timestamp

Each result contains:
- `original`: Original address
- `parsed`: Parsed address components
- `formatted`: USPS-formatted components
- `single_line`: Single-line formatted address
- `multi_line`: Multi-line formatted address
- `confidence`: Confidence score
- `valid`: Validation status
- `issues`: List of issues
- `address_type`: Address type

**With Column Preservation** (using `--preserve-columns`):
- `results`: Array of processing results (same as above)
- `original_data`: Array of original CSV rows with all original columns
- `summary`: Processing statistics
- `timestamp`: Processing timestamp

#### Excel Output

**Standard Output** (without `--preserve-columns`):
- **Addresses sheet**: Parsed address columns (Original Address, Street Number, etc.)
- **Summary sheet**: Processing statistics and metrics

**With Column Preservation** (using `--preserve-columns`):
- **Addresses sheet**: All original columns + cleaned address columns (with "Cleaned " prefix)
- **Summary sheet**: Processing statistics and metrics

## Understanding Results

### Confidence Scores

The tool provides confidence scores (0-100) to help you assess result quality:

- **90-100%**: High confidence - Results are very reliable
- **70-89%**: Medium confidence - Results are generally good, minor review recommended
- **50-69%**: Low confidence - Results may have issues, manual review recommended
- **0-49%**: Very low confidence - Results likely have significant issues

### Validation Status

- **Valid**: Address meets all validation criteria (ZIP code format, state abbreviation, completeness)
- **Invalid**: Address fails one or more validation checks

### When Manual Review is Needed

Review addresses with:
- Confidence scores below 70%
- Validation status "Invalid"
- Non-empty "issues" field
- Unusual address types or formats

### Example Interpretations

```json
{
  "original": "123 Main Street, Austin, TX 78701",
  "confidence": 90.0,
  "valid": true,
  "issues": [],
  "formatted_address": "123 MAIN ST, AUSTIN, TX, 78701"
}
```
✅ **High confidence, valid address** - Ready to use

```json
{
  "original": "123 Main St Austin TX",
  "confidence": 65.0,
  "valid": false,
  "issues": ["Missing required fields: zip_code"],
  "formatted_address": "123 MAIN ST, AUSTIN, TX"
}
```
⚠️ **Medium confidence, missing ZIP** - Add ZIP code if known

## Performance Guidelines

### Expected Processing Times

- **Single address**: ~0.4 seconds
- **Small files (100 addresses)**: ~10 seconds
- **Medium files (1,000 addresses)**: ~2 minutes
- **Large files (10,000 addresses)**: ~20 minutes

### Memory Requirements

- **Base memory**: ~50MB
- **Per 1,000 addresses**: ~5MB additional
- **Recommended**: 100MB+ available memory for files >5,000 addresses

### File Size Limitations

- **Maximum recommended**: 50,000 addresses per file
- **Chunk processing**: Automatically handles large files
- **Memory optimization**: Use smaller chunk sizes (500-1000) for very large files

### Chunk Size Recommendations

- **Small files (<1,000 addresses)**: Default (1000) is fine
- **Medium files (1,000-10,000 addresses)**: Use 1000-2000
- **Large files (>10,000 addresses)**: Use 500-1000
- **Memory-constrained systems**: Use 250-500

## Examples

### Processing a Sample File

```bash
# Process the included sample file
address-cleanser batch --input out/sample_input.csv --output results.csv --format csv --report report.txt
```

### Working with Different CSV Structures

**Example 1: CSV with separate address columns**
```bash
# Auto-detect and combine address columns, preserve all original columns
address-cleanser batch \
  --input client_data.csv \
  --output cleaned.csv \
  --preserve-columns \
  --auto-combine
```

**Example 2: Explicitly specify which columns to combine**
```bash
# Combine specific columns and preserve original structure
address-cleanser batch \
  --input data.csv \
  --output cleaned.csv \
  --preserve-columns \
  --address-columns "Address,City,State,Zip"
```

**Example 3: Combined address column (standard)**
```bash
# Standard processing with combined address column
address-cleanser batch \
  --input addresses.csv \
  --output cleaned.csv \
  --address-column "Full_Address"
```

**Example 4: Preserve columns and export to Excel**
```bash
# Maintain original structure, add cleaned fields, output to Excel
address-cleanser batch \
  --input client_data.csv \
  --output cleaned.xlsx \
  --format excel \
  --preserve-columns \
  --auto-combine
```

### Processing Different Address Types

The tool handles various address formats:

- **Standard addresses**: `123 Main Street, Austin, TX 78701`
- **PO Box addresses**: `PO Box 123, Austin, TX 78701`
- **Apartment addresses**: `123 Main St Apt 456, Austin, TX 78701`
- **Addresses with directionals**: `123 North Main Street, Austin, TX 78701`
- **ZIP+4 codes**: `123 Main St, Austin TX 78701-1234`

### Validation Examples

The tool validates:
- **ZIP codes**: Must be 5 digits or ZIP+4 format
- **State abbreviations**: Must be valid US state abbreviations
- **Address completeness**: Requires street number, street name, city, and state
- **PO Box addresses**: Have different completeness requirements

## Troubleshooting

### Common Errors and Solutions

**Error: "No such file or directory"**
- **Cause**: Input file doesn't exist or path is incorrect
- **Solution**: Check file path and ensure file exists

**Error: "Address column 'address' not found"**
- **Cause**: CSV doesn't have a column named "address" (column names are case-sensitive)
- **Solution**: 
  - Use `--address-column` to specify a single column name (e.g., `--address-column "Address"`)
  - Use `--auto-combine` to auto-detect and combine separate address columns
  - Use `--address-columns` to explicitly specify multiple columns to combine (e.g., `--address-columns "Address,City,State,Zip"`)
- **Note**: Column names are case-sensitive and must match exactly

**Error: "Invalid input file format"**
- **Cause**: File is not a CSV
- **Solution**: Ensure input file has .csv extension

**Error: "Failed to install dependencies"**
- **Cause**: pip installation issues
- **Solution**: Try manual installation or check Python/pip setup

### Platform-Specific Issues

**Linux/macOS:**
- Ensure Python 3.8+ is installed
- Use `python3` command instead of `python`

**Windows:**
- Use `python` instead of `python3`
- Ensure PATH includes Python installation

### Dependency Conflicts

**If installation fails:**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Performance Problems

**Slow processing:**
- Reduce chunk size: `--chunk-size 500`
- Check available memory
- Close other applications

**Memory errors:**
- Use smaller chunk sizes
- Process files in smaller batches
- Increase system memory if possible

## Technical Details

### Architecture

The tool uses a modular architecture with three main components:

1. **Parser** (`src/parser.py`): Uses `usaddress` library for NLP-based address parsing
2. **Validator** (`src/validator.py`): Offline validation of address components
3. **Formatter** (`src/formatter.py`): USPS Publication 28 standard formatting

### Why usaddress instead of libpostal?

The implementation uses `usaddress` instead of the originally planned `libpostal` for several reasons:

- **Easier installation**: No system-level dependencies required
- **Better Python integration**: Native Python library
- **Sufficient accuracy**: Meets requirements for US address parsing
- **Maintenance**: Actively maintained Python package

### Limitations and Accuracy

**Supported:**
- US addresses only (including territories)
- Standard street addresses
- PO Box addresses
- Apartment/suite addresses
- ZIP and ZIP+4 codes

**Not supported:**
- International addresses
- Military addresses (APO/FPO)
- Rural route addresses
- Some non-standard formats

**Typical accuracy:**
- Standard addresses: 90-95%
- PO Box addresses: 95-98%
- Apartment addresses: 85-90%
- Malformed addresses: 60-80%

### Offline Operation

The tool operates completely offline:
- No internet connection required
- No external API calls
- All validation uses built-in rules
- Fast processing without network delays

## Testing

Run the test suite:

```bash
python -m pytest tests/ -v
```

Run tests with coverage:

```bash
python -m pytest tests/ --cov=src --cov-report=html
```

## Project Structure

```
address-cleaner/
├── src/
│   ├── __init__.py
│   ├── parser.py          # Address parsing with usaddress
│   ├── validator.py       # Offline validation rules
│   ├── formatter.py       # USPS formatting standards
│   └── utils.py           # Helper functions
├── cli.py                 # CLI interface
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_validator.py
│   └── test_integration.py
├── out/                   # Sample data (contains sample_input.csv)
├── logs/                  # Runtime logs
├── requirements.txt
├── install.sh
├── run.sh
├── README.md
└── LICENSE
```

## Configuration

### Logging

The tool supports configurable logging:

```bash
# Set log level
address-cleanser --log-level DEBUG batch --input addresses.csv --output results.csv

# Log to file
address-cleanser --log-file logs/processing.log batch --input addresses.csv --output results.csv
```

### Performance

For large files, the tool processes addresses in chunks to manage memory usage. The default chunk size is 1000 addresses, but you can adjust this:

```bash
address-cleanser batch --input large_file.csv --output results.csv --chunk-size 5000
```

## Error Handling

The tool handles various error conditions gracefully:

- **Invalid input files**: Clear error messages for missing or malformed files
- **Parsing errors**: Fallback strategies for ambiguous addresses
- **Validation errors**: Detailed error messages for invalid components
- **File I/O errors**: Proper error handling for file operations

## Limitations

- **US addresses only**: The tool is designed specifically for US addresses
- **Offline validation**: No real-time USPS API validation in MVP version
- **English only**: Address parsing works best with English text

## Future Enhancements

- USPS API integration for real-time validation
- International address support
- Geocoding capabilities
- Web API endpoint
- Docker containerization

## Recent Updates

### Version 1.0.14 Features

- **Fixed PyInstaller Executable Issues**: 
  - Fixed `ModuleNotFoundError: No module named 'mmap'` that caused crashes when writing CSV output
  - Fixed address parsing failures by including usaddress model files in executable bundles
  - Executables now work correctly with all features

### Version 1.0.13 Features

- **Column Preservation**: Preserve original CSV columns with `--preserve-columns` flag
- **Auto-Detection**: Automatically detect and combine separate address columns with `--auto-combine`
- **Manual Column Combination**: Explicitly specify columns to combine with `--address-columns`
- **Enhanced Output**: Original data structure maintained while adding cleaned address fields
- **Flexible Input**: Now supports both single-column addresses and separate address components

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Support

For issues and questions, please create an issue in the project repository.# address-cleanser
