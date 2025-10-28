"""
Address validation module for offline validation of US addresses.

This module provides functionality to validate address components
against US standards without requiring external API calls.
"""

import re
from typing import Dict, Any, List, Tuple, Optional


# Valid US state abbreviations (including DC and territories)
VALID_STATES = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
    'DC', 'AS', 'GU', 'MP', 'PR', 'VI'
}

# State name to abbreviation mapping
STATE_NAME_TO_ABBREV = {
    'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR',
    'CALIFORNIA': 'CA', 'COLORADO': 'CO', 'CONNECTICUT': 'CT', 'DELAWARE': 'DE',
    'FLORIDA': 'FL', 'GEORGIA': 'GA', 'HAWAII': 'HI', 'IDAHO': 'ID',
    'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA', 'KANSAS': 'KS',
    'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD',
    'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS',
    'MISSOURI': 'MO', 'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV',
    'NEW HAMPSHIRE': 'NH', 'NEW JERSEY': 'NJ', 'NEW MEXICO': 'NM', 'NEW YORK': 'NY',
    'NORTH CAROLINA': 'NC', 'NORTH DAKOTA': 'ND', 'OHIO': 'OH', 'OKLAHOMA': 'OK',
    'OREGON': 'OR', 'PENNSYLVANIA': 'PA', 'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC',
    'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'TEXAS': 'TX', 'UTAH': 'UT',
    'VERMONT': 'VT', 'VIRGINIA': 'VA', 'WASHINGTON': 'WA', 'WEST VIRGINIA': 'WV',
    'WISCONSIN': 'WI', 'WYOMING': 'WY', 'DISTRICT OF COLUMBIA': 'DC',
    'AMERICAN SAMOA': 'AS', 'GUAM': 'GU', 'NORTHERN MARIANA ISLANDS': 'MP',
    'PUERTO RICO': 'PR', 'VIRGIN ISLANDS': 'VI'
}


def validate_zip_code(zip_code: str) -> Tuple[bool, str]:
    """
    Validate ZIP code format (5-digit or ZIP+4).
    
    Args:
        zip_code: ZIP code string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not zip_code:
        return False, "ZIP code is missing"
    
    # Remove any non-digit characters except hyphens
    cleaned_zip = re.sub(r'[^\d-]', '', zip_code.strip())
    
    # Check for 5-digit ZIP code
    if re.match(r'^\d{5}$', cleaned_zip):
        return True, ""
    
    # Check for ZIP+4 format (12345-6789)
    if re.match(r'^\d{5}-\d{4}$', cleaned_zip):
        return True, ""
    
    return False, f"Invalid ZIP code format: {zip_code}. Expected 5 digits or ZIP+4 format (12345-6789)"


def validate_state(state: str) -> Tuple[bool, str]:
    """
    Validate state abbreviation or name.
    
    Args:
        state: State abbreviation or name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not state:
        return False, "State is missing"
    
    state_upper = state.upper().strip()
    
    # Check if it's a valid abbreviation
    if state_upper in VALID_STATES:
        return True, ""
    
    # Check if it's a valid state name
    if state_upper in STATE_NAME_TO_ABBREV:
        return True, ""
    
    return False, f"Invalid state: {state}. Must be a valid US state abbreviation or name"


def validate_address_completeness(address_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that an address has the required components for completeness.
    
    Args:
        address_dict: Dictionary containing address components
        
    Returns:
        Tuple of (is_complete, list_of_missing_fields)
    """
    if not address_dict:
        return False, ['street_number', 'street_name', 'city', 'state']
    
    missing_fields = []
    
    # Required fields for a complete address
    required_fields = ['street_number', 'street_name', 'city', 'state']
    
    # Check for required fields
    for field in required_fields:
        if not address_dict.get(field):
            missing_fields.append(field)
    
    # Special case: PO Box addresses don't need street number/name
    if address_dict.get('po_box'):
        po_box_required = ['po_box', 'city', 'state']
        po_box_missing = [field for field in po_box_required if not address_dict.get(field)]
        if not po_box_missing:
            return True, []
    
    is_complete = len(missing_fields) == 0
    return is_complete, missing_fields


def calculate_confidence_score(parsed: Dict[str, Any], validations: Dict[str, Any]) -> float:
    """
    Calculate overall confidence score based on parsing and validation results.
    
    Args:
        parsed: Parsed address components
        validations: Validation results
        
    Returns:
        Confidence score between 0.0 and 100.0
    """
    if not parsed or not validations:
        return 0.0
    
    # Start with parsing confidence
    base_confidence = parsed.get('confidence', 0.0)
    
    # Adjust based on validation results
    adjustments = []
    
    # ZIP code validation
    zip_valid = validations.get('zip_valid', False)
    adjustments.append(10.0 if zip_valid else -20.0)
    
    # State validation
    state_valid = validations.get('state_valid', False)
    adjustments.append(10.0 if state_valid else -20.0)
    
    # Address completeness
    is_complete = validations.get('is_complete', False)
    adjustments.append(15.0 if is_complete else -25.0)
    
    # Calculate final score
    final_score = base_confidence + sum(adjustments)
    
    # Ensure score is within bounds
    return max(0.0, min(100.0, final_score))


def validate_address(address_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform comprehensive validation of an address.
    
    Args:
        address_dict: Dictionary containing address components
        
    Returns:
        Dictionary containing validation results
    """
    if not address_dict:
        return {
            'valid': False,
            'zip_valid': False,
            'state_valid': False,
            'is_complete': False,
            'confidence': 0.0,
            'issues': ['Address dictionary is empty']
        }
    
    issues = []
    
    # Validate ZIP code
    zip_code = address_dict.get('zip_code', '')
    zip_valid, zip_error = validate_zip_code(zip_code)
    if not zip_valid:
        issues.append(zip_error)
    
    # Validate state
    state = address_dict.get('state', '')
    state_valid, state_error = validate_state(state)
    if not state_valid:
        issues.append(state_error)
    
    # Check completeness
    is_complete, missing_fields = validate_address_completeness(address_dict)
    if not is_complete:
        issues.append(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Calculate overall confidence
    confidence = calculate_confidence_score(address_dict, {
        'zip_valid': zip_valid,
        'state_valid': state_valid,
        'is_complete': is_complete
    })
    
    # Determine overall validity
    valid = zip_valid and state_valid and is_complete
    
    return {
        'valid': valid,
        'zip_valid': zip_valid,
        'state_valid': state_valid,
        'is_complete': is_complete,
        'confidence': confidence,
        'issues': issues,
        'missing_fields': missing_fields if not is_complete else []
    }


def validate_street_number(street_number: str) -> Tuple[bool, str]:
    """
    Validate street number format.
    
    Args:
        street_number: Street number to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not street_number:
        return False, "Street number is missing"
    
    # Remove any non-digit characters
    cleaned_number = re.sub(r'[^\d]', '', street_number.strip())
    
    # Check if it's a valid number
    if not cleaned_number:
        return False, f"Invalid street number: {street_number}. Must contain digits"
    
    # Check reasonable range (1 to 99999)
    try:
        num = int(cleaned_number)
        if 1 <= num <= 99999:
            return True, ""
        else:
            return False, f"Street number out of range: {street_number}. Must be between 1 and 99999"
    except ValueError:
        return False, f"Invalid street number format: {street_number}"


def validate_city(city: str) -> Tuple[bool, str]:
    """
    Validate city name format.
    
    Args:
        city: City name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not city:
        return False, "City is missing"
    
    city_clean = city.strip()
    
    # Check minimum length
    if len(city_clean) < 2:
        return False, f"City name too short: {city}. Must be at least 2 characters"
    
    # Check maximum length
    if len(city_clean) > 50:
        return False, f"City name too long: {city}. Must be 50 characters or less"
    
    # Check for valid characters (letters, spaces, hyphens, apostrophes)
    if not re.match(r"^[A-Za-z\s\-']+$", city_clean):
        return False, f"City name contains invalid characters: {city}. Only letters, spaces, hyphens, and apostrophes allowed"
    
    return True, ""


def get_state_abbreviation(state_input: str) -> Optional[str]:
    """
    Get state abbreviation from state name or abbreviation.
    
    Args:
        state_input: State name or abbreviation
        
    Returns:
        State abbreviation if valid, None otherwise
    """
    if not state_input:
        return None
    
    state_upper = state_input.upper().strip()
    
    # If it's already an abbreviation, return it
    if state_upper in VALID_STATES:
        return state_upper
    
    # If it's a state name, convert to abbreviation
    if state_upper in STATE_NAME_TO_ABBREV:
        return STATE_NAME_TO_ABBREV[state_upper]
    
    return None
