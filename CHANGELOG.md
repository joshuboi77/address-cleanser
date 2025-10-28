# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-28

### Added
- Initial release with address parsing, validation, and formatting
- Support for CSV, JSON, and Excel output formats
- Batch and single address processing modes
- Comprehensive test suite with 62 tests
- CLI interface with Click framework
- USPS Publication 28 standard formatting
- Offline validation for ZIP codes and state abbreviations
- Progress tracking for batch processing
- Configurable logging system
- Installation script for easy setup

### Fixed
- CLI batch processing bug with empty directory paths
- Street type abbreviation issue in formatter
- Error handling in directory creation utilities

### Technical Details
- Uses `usaddress` library for NLP-based address parsing
- Modular architecture with parser, validator, and formatter components
- Comprehensive error handling and fallback strategies
- Support for various address types (street, PO Box, apartment)

### Known Issues
- Performance benchmarks pending validation
- No international address support
- No real-time USPS API validation

### Dependencies
- Python 3.8+
- usaddress>=0.5.16
- pandas>=2.0.0
- openpyxl>=3.0.0
- click>=8.0.0
- tqdm>=4.60.0
