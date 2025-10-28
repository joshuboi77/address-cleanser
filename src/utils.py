"""
Utility functions for the Address Cleanser package.

This module provides helper functions for logging, file I/O operations,
and common data processing tasks.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path. If None, logs to console only.
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("address_cleanser")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory
    """
    if directory_path and directory_path.strip():
        os.makedirs(directory_path, exist_ok=True)


def clean_string(text: str) -> str:
    """
    Clean and normalize a string by removing extra whitespace and converting to uppercase.
    
    Args:
        text: Input string to clean
        
    Returns:
        Cleaned string
    """
    if not text:
        return ""
    
    # Remove extra whitespace and convert to uppercase
    return " ".join(str(text).strip().split()).upper()


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = "") -> Any:
    """
    Safely get a value from a dictionary with a default fallback.
    
    Args:
        dictionary: Dictionary to search
        key: Key to look for
        default: Default value if key not found
        
    Returns:
        Value from dictionary or default
    """
    return dictionary.get(key, default) if dictionary else default


def format_timestamp() -> str:
    """
    Get current timestamp as a formatted string.
    
    Returns:
        Formatted timestamp string
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def validate_file_extension(file_path: str, allowed_extensions: List[str]) -> bool:
    """
    Validate that a file has an allowed extension.
    
    Args:
        file_path: Path to the file
        allowed_extensions: List of allowed file extensions (with dots)
        
    Returns:
        True if file extension is allowed, False otherwise
    """
    if not file_path:
        return False
    
    file_ext = os.path.splitext(file_path)[1].lower()
    return file_ext in [ext.lower() for ext in allowed_extensions]


def read_json_file(file_path: str) -> Dict[str, Any]:
    """
    Read and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON data as dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json_file(data: Dict[str, Any], file_path: str) -> None:
    """
    Write data to a JSON file with proper formatting.
    
    Args:
        data: Data to write
        file_path: Path to the output file
    """
    ensure_directory_exists(os.path.dirname(file_path))
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def calculate_processing_stats(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate processing statistics from a list of results.
    
    Args:
        results: List of processing results
        
    Returns:
        Dictionary containing processing statistics
    """
    if not results:
        return {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "success_rate": 0.0,
            "average_confidence": 0.0
        }
    
    total = len(results)
    successful = sum(1 for r in results if r.get("valid", False))
    failed = total - successful
    success_rate = (successful / total) * 100 if total > 0 else 0.0
    
    # Calculate average confidence
    confidences = [r.get("confidence", 0) for r in results if isinstance(r.get("confidence"), (int, float))]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    
    return {
        "total_processed": total,
        "successful": successful,
        "failed": failed,
        "success_rate": round(success_rate, 2),
        "average_confidence": round(avg_confidence, 2)
    }
