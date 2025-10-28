"""
Address parsing module using the usaddress library.

This module provides functionality to parse unstructured US address strings
into standardized components using the usaddress NLP-based parser.
"""

import re
import usaddress
from typing import Dict, Any, Optional, Tuple
from .utils import clean_string, safe_get


def parse_address(raw_address: str) -> Dict[str, Any]:
    """
    Parse a raw address string into structured components.
    
    Args:
        raw_address: Raw address string to parse
        
    Returns:
        Dictionary containing parsed address components and metadata
    """
    if not raw_address or not isinstance(raw_address, str):
        return {
            "original": raw_address or "",
            "parsed": {},
            "confidence": 0.0,
            "error": "Invalid input: empty or non-string address"
        }
    
    # Clean the input address
    cleaned_address = clean_string(raw_address)
    
    try:
        # Parse using usaddress
        parsed_components, address_type = usaddress.tag(cleaned_address)
        
        # Calculate confidence based on parsing success and component completeness
        confidence = _calculate_parsing_confidence(parsed_components, address_type)
        
        return {
            "original": raw_address,
            "parsed": parsed_components,
            "address_type": address_type,
            "confidence": confidence,
            "error": None
        }
        
    except usaddress.RepeatedLabelError as e:
        # Handle ambiguous addresses by trying alternative parsing
        return _handle_repeated_label_error(cleaned_address, raw_address, str(e))
        
    except Exception as e:
        return {
            "original": raw_address,
            "parsed": {},
            "confidence": 0.0,
            "error": f"Parsing error: {str(e)}"
        }


def normalize_components(parsed: Dict[str, str]) -> Dict[str, str]:
    """
    Normalize and standardize parsed address components.
    
    Args:
        parsed: Dictionary of parsed address components
        
    Returns:
        Dictionary with normalized components
    """
    if not parsed:
        return {}
    
    normalized = {}
    
    # Map usaddress labels to our standard field names
    field_mapping = {
        'AddressNumber': 'street_number',
        'StreetName': 'street_name',
        'StreetNamePreDirectional': 'street_directional_prefix',
        'StreetNamePostDirectional': 'street_directional_suffix',
        'StreetNamePostModifier': 'street_type',
        'StreetNamePostType': 'street_type',  # Alternative field name used by usaddress
        'OccupancyType': 'unit_type',
        'OccupancyIdentifier': 'unit_number',
        'PlaceName': 'city',
        'StateName': 'state',
        'ZipCode': 'zip_code',
        'ZipPlus4': 'zip_plus4',
        'POBox': 'po_box',
        'USPSBoxID': 'po_box',
        'USPSBoxType': 'po_box_type'
    }
    
    # Normalize each component
    for usaddress_label, our_field in field_mapping.items():
        if usaddress_label in parsed:
            value = parsed[usaddress_label]
            if value:
                # Special handling for PO Box fields
                if usaddress_label in ['USPSBoxID', 'USPSBoxType']:
                    if 'po_box' not in normalized:
                        normalized['po_box'] = clean_string(value)
                    elif usaddress_label == 'USPSBoxID':
                        normalized['po_box'] = clean_string(value)
                else:
                    normalized[our_field] = clean_string(value)
    
    # Handle special cases
    _normalize_special_cases(normalized, parsed)
    
    return normalized


def handle_edge_cases(address: str) -> str:
    """
    Pre-process addresses to handle common edge cases before parsing.
    
    Args:
        address: Raw address string
        
    Returns:
        Pre-processed address string
    """
    if not address:
        return ""
    
    # Remove extra whitespace and normalize
    processed = clean_string(address)
    
    # Handle common abbreviations and variations
    replacements = {
        r'\bSTREET\b': 'ST',
        r'\bAVENUE\b': 'AVE',
        r'\bBOULEVARD\b': 'BLVD',
        r'\bROAD\b': 'RD',
        r'\bDRIVE\b': 'DR',
        r'\bLANE\b': 'LN',
        r'\bCOURT\b': 'CT',
        r'\bPLACE\b': 'PL',
        r'\bNORTH\b': 'N',
        r'\bSOUTH\b': 'S',
        r'\bEAST\b': 'E',
        r'\bWEST\b': 'W',
        r'\bAPARTMENT\b': 'APT',
        r'\bSUITE\b': 'STE',
        r'\bUNIT\b': 'UNIT',
        r'\bFLOOR\b': 'FL'
    }
    
    for pattern, replacement in replacements.items():
        processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)
    
    # Clean up extra spaces around commas
    processed = re.sub(r'\s*,\s*', ', ', processed)
    
    # Handle PO Box variations
    po_box_patterns = [
        r'\bP\.?O\.?\s*BOX\b',
        r'\bPOST\s*OFFICE\s*BOX\b',
        r'\bPO\s*BOX\b'
    ]
    
    for pattern in po_box_patterns:
        processed = re.sub(pattern, 'PO BOX', processed, flags=re.IGNORECASE)
    
    return processed


def _calculate_parsing_confidence(parsed_components: Dict[str, str], address_type: str) -> float:
    """
    Calculate confidence score based on parsing results.
    
    Args:
        parsed_components: Parsed address components
        address_type: Type of address (Street Address, PO Box, etc.)
        
    Returns:
        Confidence score between 0.0 and 100.0
    """
    if not parsed_components:
        return 0.0
    
    # Base score
    score = 50.0
    
    # Required components for a complete address
    required_fields = ['AddressNumber', 'StreetName', 'PlaceName', 'StateName']
    optional_fields = ['ZipCode', 'StreetNamePostModifier']
    
    # Check for required fields
    required_present = sum(1 for field in required_fields if field in parsed_components)
    score += (required_present / len(required_fields)) * 30.0
    
    # Check for optional fields
    optional_present = sum(1 for field in optional_fields if field in parsed_components)
    score += (optional_present / len(optional_fields)) * 20.0
    
    # Bonus for PO Box addresses (they have different requirements)
    if address_type == "PO Box":
        if 'POBox' in parsed_components and 'PlaceName' in parsed_components:
            score += 10.0
    
    return min(score, 100.0)


def _handle_repeated_label_error(cleaned_address: str, original_address: str, error_msg: str) -> Dict[str, Any]:
    """
    Handle RepeatedLabelError by attempting alternative parsing strategies.
    
    Args:
        cleaned_address: Cleaned address string
        original_address: Original address string
        error_msg: Error message from usaddress
        
    Returns:
        Dictionary with parsing results or error information
    """
    try:
        # Try parsing with different strategies
        strategies = [
            # Strategy 1: Remove common problematic words
            lambda addr: re.sub(r'\b(AND|&)\b', '', addr, flags=re.IGNORECASE),
            # Strategy 2: Split on commas and take the first part
            lambda addr: addr.split(',')[0] if ',' in addr else addr,
            # Strategy 3: Remove extra spaces around punctuation
            lambda addr: re.sub(r'\s*,\s*', ', ', addr)
        ]
        
        for i, strategy in enumerate(strategies):
            try:
                modified_address = strategy(cleaned_address)
                parsed_components, address_type = usaddress.tag(modified_address)
                confidence = _calculate_parsing_confidence(parsed_components, address_type)
                
                return {
                    "original": original_address,
                    "parsed": parsed_components,
                    "address_type": address_type,
                    "confidence": confidence * 0.8,  # Reduce confidence for alternative parsing
                    "error": None,
                    "parsing_strategy": f"alternative_{i+1}"
                }
            except usaddress.RepeatedLabelError:
                continue
            except Exception:
                continue
        
        # If all strategies fail, return error
        return {
            "original": original_address,
            "parsed": {},
            "confidence": 0.0,
            "error": f"Could not parse address: {error_msg}"
        }
        
    except Exception as e:
        return {
            "original": original_address,
            "parsed": {},
            "confidence": 0.0,
            "error": f"Error handling repeated labels: {str(e)}"
        }


def _normalize_special_cases(normalized: Dict[str, str], parsed: Dict[str, str]) -> None:
    """
    Handle special cases in address normalization.
    
    Args:
        normalized: Dictionary to update with normalized values
        parsed: Original parsed components
    """
    # Combine street name components
    street_parts = []
    if 'StreetNamePreDirectional' in parsed:
        street_parts.append(clean_string(parsed['StreetNamePreDirectional']))
    if 'StreetName' in parsed:
        street_parts.append(clean_string(parsed['StreetName']))
    if 'StreetNamePostDirectional' in parsed:
        street_parts.append(clean_string(parsed['StreetNamePostDirectional']))
    
    if street_parts:
        normalized['street_name'] = ' '.join(street_parts)
    
    # Handle ZIP+4 codes
    if 'ZipCode' in parsed and 'ZipPlus4' in parsed:
        zip_code = parsed['ZipCode']
        zip_plus4 = parsed['ZipPlus4']
        normalized['zip_code'] = f"{zip_code}-{zip_plus4}"
    elif 'ZipCode' in parsed:
        normalized['zip_code'] = parsed['ZipCode']
    
    # Handle unit information
    if 'OccupancyType' in parsed and 'OccupancyIdentifier' in parsed:
        unit_type = clean_string(parsed['OccupancyType'])
        unit_number = parsed['OccupancyIdentifier']
        normalized['unit'] = f"{unit_type} {unit_number}"
    elif 'OccupancyIdentifier' in parsed:
        normalized['unit'] = parsed['OccupancyIdentifier']
