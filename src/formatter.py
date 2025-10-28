"""
Address formatting module for USPS Publication 28 standards.

This module provides functionality to format addresses according to
USPS Publication 28 standards for optimal mail delivery.
"""

from typing import Dict, Any, List, Optional
from .utils import clean_string
from .parser import normalize_components


# USPS standard abbreviations for street types
STREET_TYPE_ABBREVIATIONS = {
    'ALLEY': 'ALY',
    'ANEX': 'ANX',
    'ANNEX': 'ANX',
    'ARCADE': 'ARC',
    'AVENUE': 'AVE',
    'BAYOU': 'BYU',
    'BEACH': 'BCH',
    'BEND': 'BND',
    'BLUFF': 'BLF',
    'BLUFFS': 'BLFS',
    'BOTTOM': 'BTM',
    'BOULEVARD': 'BLVD',
    'BRANCH': 'BR',
    'BRIDGE': 'BRG',
    'BROOK': 'BRK',
    'BROOKS': 'BRKS',
    'BURG': 'BG',
    'BURGS': 'BGS',
    'BYPASS': 'BYP',
    'BYWAY': 'BYW',
    'CAMP': 'CP',
    'CANYON': 'CYN',
    'CAPE': 'CPE',
    'CAUSEWAY': 'CSWY',
    'CENTER': 'CTR',
    'CENTERS': 'CTRS',
    'CIRCLE': 'CIR',
    'CIRCLES': 'CIRS',
    'CLIFF': 'CLF',
    'CLIFFS': 'CLFS',
    'CLOSE': 'CL',
    'CLUB': 'CLB',
    'COMMON': 'CMN',
    'COMMONS': 'CMNS',
    'CORNER': 'COR',
    'CORNERS': 'CORS',
    'COURSE': 'CRSE',
    'COURT': 'CT',
    'COURTS': 'CTS',
    'COVE': 'CV',
    'COVES': 'CVS',
    'CREEK': 'CRK',
    'CRESCENT': 'CRES',
    'CREST': 'CRST',
    'CROSSING': 'XING',
    'CROSSROAD': 'XRD',
    'CROSSROADS': 'XRDS',
    'CURVE': 'CURV',
    'DALE': 'DL',
    'DAM': 'DM',
    'DIVIDE': 'DV',
    'DRIVE': 'DR',
    'DRIVES': 'DRS',
    'ESTATE': 'EST',
    'ESTATES': 'ESTS',
    'EXPRESSWAY': 'EXPY',
    'EXTENSION': 'EXT',
    'EXTENSIONS': 'EXTS',
    'FALL': 'FALL',
    'FALLS': 'FLS',
    'FERRY': 'FRY',
    'FIELD': 'FLD',
    'FIELDS': 'FLDS',
    'FLAT': 'FLT',
    'FLATS': 'FLTS',
    'FORD': 'FRD',
    'FORDS': 'FRDS',
    'FOREST': 'FRST',
    'FORGE': 'FRG',
    'FORGES': 'FRGS',
    'FORK': 'FRK',
    'FORKS': 'FRKS',
    'FORT': 'FT',
    'FREEWAY': 'FWY',
    'GARDEN': 'GDN',
    'GARDENS': 'GDNS',
    'GATEWAY': 'GTWY',
    'GLEN': 'GLN',
    'GLENS': 'GLNS',
    'GREEN': 'GRN',
    'GREENS': 'GRNS',
    'GROVE': 'GRV',
    'GROVES': 'GRVS',
    'HARBOR': 'HBR',
    'HARBORS': 'HBRS',
    'HAVEN': 'HVN',
    'HEIGHTS': 'HTS',
    'HIGHWAY': 'HWY',
    'HILL': 'HL',
    'HILLS': 'HLS',
    'HOLLOW': 'HOLW',
    'INLET': 'INLT',
    'ISLAND': 'IS',
    'ISLANDS': 'ISS',
    'ISLE': 'ISLE',
    'JUNCTION': 'JCT',
    'JUNCTIONS': 'JCTS',
    'KEY': 'KY',
    'KEYS': 'KYS',
    'KNOLL': 'KNL',
    'KNOLLS': 'KNLS',
    'LAKE': 'LK',
    'LAKES': 'LKS',
    'LAND': 'LAND',
    'LANDING': 'LNDG',
    'LANE': 'LN',
    'LANES': 'LNS',
    'LIGHT': 'LGT',
    'LIGHTS': 'LGTS',
    'LOAF': 'LF',
    'LOCK': 'LCK',
    'LOCKS': 'LCKS',
    'LODGE': 'LDG',
    'LOOP': 'LOOP',
    'MALL': 'MALL',
    'MANOR': 'MNR',
    'MANORS': 'MNRS',
    'MEADOW': 'MDW',
    'MEADOWS': 'MDWS',
    'MILE': 'MI',
    'MILES': 'MIS',
    'MILL': 'ML',
    'MILLS': 'MLS',
    'MISSION': 'MSN',
    'MOUNT': 'MT',
    'MOUNTAIN': 'MTN',
    'MOUNTAINS': 'MTNS',
    'NECK': 'NCK',
    'ORCHARD': 'ORCH',
    'OVAL': 'OVAL',
    'OVERPASS': 'OPAS',
    'PARK': 'PARK',
    'PARKS': 'PARK',
    'PARKWAY': 'PKWY',
    'PARKWAYS': 'PKWY',
    'PASS': 'PASS',
    'PASSAGE': 'PSGE',
    'PATH': 'PATH',
    'PIKE': 'PIKE',
    'PINE': 'PNE',
    'PINES': 'PNES',
    'PLACE': 'PL',
    'PLAIN': 'PLN',
    'PLAINS': 'PLNS',
    'PLAZA': 'PLZ',
    'POINT': 'PT',
    'POINTS': 'PTS',
    'PORT': 'PRT',
    'PORTS': 'PRTS',
    'PRAIRIE': 'PR',
    'RADIAL': 'RADL',
    'RAMP': 'RAMP',
    'RANCH': 'RNCH',
    'RAPID': 'RPD',
    'RAPIDS': 'RPDS',
    'REST': 'RST',
    'RIDGE': 'RDG',
    'RIDGES': 'RDGS',
    'RIVER': 'RIV',
    'ROAD': 'RD',
    'ROADS': 'RDS',
    'ROUTE': 'RTE',
    'ROW': 'ROW',
    'RUE': 'RUE',
    'RUN': 'RUN',
    'SHOAL': 'SHL',
    'SHOALS': 'SHLS',
    'SHORE': 'SHR',
    'SHORES': 'SHRS',
    'SKYWAY': 'SKWY',
    'SPRING': 'SPG',
    'SPRINGS': 'SPGS',
    'SPUR': 'SPUR',
    'SQUARE': 'SQ',
    'SQUARES': 'SQS',
    'STATION': 'STA',
    'STRAVENUE': 'STRA',
    'STREAM': 'STRM',
    'STREET': 'ST',
    'STREETS': 'STS',
    'SUMMIT': 'SMT',
    'TERRACE': 'TER',
    'THROUGHWAY': 'TRWY',
    'TRAIL': 'TRL',
    'TRAILER': 'TRLR',
    'TUNNEL': 'TUNL',
    'TURNPIKE': 'TPKE',
    'UNDERPASS': 'UPAS',
    'UNION': 'UN',
    'UNIONS': 'UNS',
    'VALLEY': 'VLY',
    'VALLEYS': 'VLYS',
    'VIADUCT': 'VIA',
    'VIEW': 'VW',
    'VIEWS': 'VWS',
    'VILLAGE': 'VLG',
    'VILLAGES': 'VLGS',
    'VILLE': 'VL',
    'VISTA': 'VIS',
    'WALK': 'WALK',
    'WALKS': 'WALK',
    'WALL': 'WALL',
    'WAY': 'WAY',
    'WAYS': 'WAYS',
    'WELL': 'WL',
    'WELLS': 'WLS'
}

# USPS standard abbreviations for directional indicators
DIRECTIONAL_ABBREVIATIONS = {
    'NORTH': 'N',
    'NORTHEAST': 'NE',
    'EAST': 'E',
    'SOUTHEAST': 'SE',
    'SOUTH': 'S',
    'SOUTHWEST': 'SW',
    'WEST': 'W',
    'NORTHWEST': 'NW'
}

# USPS standard abbreviations for unit designators
UNIT_ABBREVIATIONS = {
    'APARTMENT': 'APT',
    'BASEMENT': 'BSMT',
    'BUILDING': 'BLDG',
    'DEPARTMENT': 'DEPT',
    'FLOOR': 'FL',
    'FRONT': 'FRNT',
    'HANGAR': 'HNGR',
    'LOBBY': 'LBBY',
    'LOT': 'LOT',
    'LOWER': 'LOWR',
    'OFFICE': 'OFC',
    'PENTHOUSE': 'PH',
    'PIER': 'PIER',
    'REAR': 'REAR',
    'ROOM': 'RM',
    'SIDE': 'SIDE',
    'SPACE': 'SPC',
    'STOP': 'STOP',
    'SUITE': 'STE',
    'TRAILER': 'TRLR',
    'UNIT': 'UNIT',
    'UPPER': 'UPPR'
}


def format_usps_standard(address_dict: Dict[str, Any]) -> Dict[str, str]:
    """
    Format address components according to USPS Publication 28 standards.
    
    Args:
        address_dict: Dictionary containing address components
        
    Returns:
        Dictionary with USPS-formatted components
    """
    if not address_dict:
        return {}
    
    formatted = {}
    
    # Format street number
    if address_dict.get('street_number'):
        formatted['street_number'] = address_dict['street_number']
    
    # Format street name with directionals and type
    street_parts = []
    
    # Add directional prefix
    if address_dict.get('street_directional_prefix'):
        directional = standardize_abbreviations(address_dict['street_directional_prefix'])
        street_parts.append(directional)
    
    # Add street name
    if address_dict.get('street_name'):
        street_parts.append(address_dict['street_name'])
    
    # Add directional suffix
    if address_dict.get('street_directional_suffix'):
        directional = standardize_abbreviations(address_dict['street_directional_suffix'])
        street_parts.append(directional)
    
    # Add street type
    if address_dict.get('street_type'):
        street_type = standardize_abbreviations(address_dict['street_type'])
        street_parts.append(street_type)
    
    if street_parts:
        formatted['street_name'] = ' '.join(street_parts)
    
    # Format unit information
    if address_dict.get('unit'):
        formatted['unit'] = standardize_unit_designator(address_dict['unit'])
    elif address_dict.get('unit_type') and address_dict.get('unit_number'):
        unit_type = standardize_abbreviations(address_dict['unit_type'])
        formatted['unit'] = f"{unit_type} {address_dict['unit_number']}"
    
    # Format PO Box
    if address_dict.get('po_box'):
        formatted['po_box'] = f"PO BOX {address_dict['po_box']}"
    
    # Format city (uppercase)
    if address_dict.get('city'):
        formatted['city'] = address_dict['city'].upper()
    
    # Format state (uppercase)
    if address_dict.get('state'):
        formatted['state'] = address_dict['state'].upper()
    
    # Format ZIP code
    if address_dict.get('zip_code'):
        formatted['zip_code'] = address_dict['zip_code']
    
    return formatted


def standardize_abbreviations(text: str) -> str:
    """
    Convert text to USPS standard abbreviations.
    
    Args:
        text: Text to standardize
        
    Returns:
        Standardized abbreviation
    """
    if not text:
        return ""
    
    text_upper = text.upper().strip()
    
    # Check street type abbreviations
    if text_upper in STREET_TYPE_ABBREVIATIONS:
        return STREET_TYPE_ABBREVIATIONS[text_upper]
    
    # Check directional abbreviations
    if text_upper in DIRECTIONAL_ABBREVIATIONS:
        return DIRECTIONAL_ABBREVIATIONS[text_upper]
    
    # Check unit abbreviations
    if text_upper in UNIT_ABBREVIATIONS:
        return UNIT_ABBREVIATIONS[text_upper]
    
    # If no abbreviation found, return uppercase text
    return text_upper


def standardize_unit_designator(unit_text: str) -> str:
    """
    Standardize unit designator text.
    
    Args:
        unit_text: Unit designator text (e.g., "Apt 123", "Suite 456")
        
    Returns:
        Standardized unit designator
    """
    if not unit_text:
        return ""
    
    unit_upper = unit_text.upper().strip()
    
    # Split into words
    words = unit_upper.split()
    
    if len(words) >= 2:
        # First word should be the unit type
        unit_type = words[0]
        unit_number = ' '.join(words[1:])
        
        # Standardize the unit type
        standardized_type = standardize_abbreviations(unit_type)
        
        return f"{standardized_type} {unit_number}"
    
    return unit_upper


def format_output_line(address_dict: Dict[str, str]) -> str:
    """
    Generate a single-line formatted address string.
    
    Args:
        address_dict: Dictionary containing formatted address components
        
    Returns:
        Single-line formatted address string
    """
    if not address_dict:
        return ""
    
    parts = []
    
    # Add street number and name
    if address_dict.get('street_number') and address_dict.get('street_name'):
        parts.append(f"{address_dict['street_number']} {address_dict['street_name']}")
    elif address_dict.get('street_name'):
        parts.append(address_dict['street_name'])
    
    # Add unit information
    if address_dict.get('unit'):
        parts.append(address_dict['unit'])
    
    # Add PO Box (alternative to street address)
    if address_dict.get('po_box'):
        parts.append(address_dict['po_box'])
    
    # Add city, state, ZIP
    city_state_zip = []
    if address_dict.get('city'):
        city_state_zip.append(address_dict['city'])
    if address_dict.get('state'):
        city_state_zip.append(address_dict['state'])
    if address_dict.get('zip_code'):
        city_state_zip.append(address_dict['zip_code'])
    
    if city_state_zip:
        parts.append(', '.join(city_state_zip))
    
    return ', '.join(parts)


def format_multi_line_address(address_dict: Dict[str, str]) -> List[str]:
    """
    Generate a multi-line formatted address for mail delivery.
    
    Args:
        address_dict: Dictionary containing formatted address components
        
    Returns:
        List of address lines
    """
    if not address_dict:
        return []
    
    lines = []
    
    # Line 1: Street address or PO Box
    if address_dict.get('po_box'):
        lines.append(address_dict['po_box'])
    else:
        line1_parts = []
        if address_dict.get('street_number') and address_dict.get('street_name'):
            line1_parts.append(f"{address_dict['street_number']} {address_dict['street_name']}")
        elif address_dict.get('street_name'):
            line1_parts.append(address_dict['street_name'])
        
        if address_dict.get('unit'):
            line1_parts.append(address_dict['unit'])
        
        if line1_parts:
            lines.append(' '.join(line1_parts))
    
    # Line 2: City, State ZIP
    city_state_zip = []
    if address_dict.get('city'):
        city_state_zip.append(address_dict['city'])
    if address_dict.get('state'):
        city_state_zip.append(address_dict['state'])
    if address_dict.get('zip_code'):
        city_state_zip.append(address_dict['zip_code'])
    
    if city_state_zip:
        lines.append(' '.join(city_state_zip))
    
    return lines


def create_formatted_address_result(original_address: str, parsed: Dict[str, Any], 
                                 validated: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a complete formatted address result combining parsing, validation, and formatting.
    
    Args:
        original_address: Original address string
        parsed: Parsed address components
        validated: Validation results
        
    Returns:
        Complete formatted address result
    """
    # Normalize parsed components
    normalized = normalize_components(parsed.get('parsed', {}))
    
    # Format according to USPS standards
    formatted_components = format_usps_standard(normalized)
    
    # Generate output formats
    single_line = format_output_line(formatted_components)
    multi_line = format_multi_line_address(formatted_components)
    
    return {
        'original': original_address,
        'parsed': normalized,
        'formatted': formatted_components,
        'single_line': single_line,
        'multi_line': multi_line,
        'confidence': parsed.get('confidence', 0.0),
        'valid': validated.get('valid', False),
        'issues': validated.get('issues', []),
        'address_type': parsed.get('address_type', 'Unknown')
    }
