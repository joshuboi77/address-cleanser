"""
Test module for the parser functionality.
"""

import pytest
from src.parser import parse_address, normalize_components, handle_edge_cases


class TestParseAddress:
    """Test cases for parse_address function."""
    
    def test_parse_standard_address(self):
        """Test parsing a standard street address."""
        address = "123 Main Street, Austin, TX 78701"
        result = parse_address(address)
        
        assert result['original'] == address
        assert result['confidence'] > 0
        assert result['error'] is None
        assert 'AddressNumber' in result['parsed']
        assert 'StreetName' in result['parsed']
        assert 'PlaceName' in result['parsed']
        assert 'StateName' in result['parsed']
        assert 'ZipCode' in result['parsed']
    
    def test_parse_po_box_address(self):
        """Test parsing a PO Box address."""
        address = "PO Box 123, Austin, TX 78701"
        result = parse_address(address)
        
        assert result['original'] == address
        assert result['confidence'] > 0
        assert result['error'] is None
        assert 'USPSBoxID' in result['parsed'] or 'POBox' in result['parsed']
        assert 'PlaceName' in result['parsed']
    
    def test_parse_apartment_address(self):
        """Test parsing an address with apartment number."""
        address = "123 Main St Apt 456, Austin, TX 78701"
        result = parse_address(address)
        
        assert result['original'] == address
        assert result['confidence'] > 0
        assert result['error'] is None
        assert 'AddressNumber' in result['parsed']
        assert 'OccupancyIdentifier' in result['parsed']
    
    def test_parse_empty_address(self):
        """Test parsing an empty address."""
        result = parse_address("")
        
        assert result['original'] == ""
        assert result['confidence'] == 0.0
        assert result['error'] == "Invalid input: empty or non-string address"
    
    def test_parse_none_address(self):
        """Test parsing None address."""
        result = parse_address(None)
        
        assert result['original'] == ""
        assert result['confidence'] == 0.0
        assert result['error'] == "Invalid input: empty or non-string address"
    
    def test_parse_invalid_type(self):
        """Test parsing non-string input."""
        result = parse_address(123)
        
        assert result['original'] == 123
        assert result['confidence'] == 0.0
        assert result['error'] == "Invalid input: empty or non-string address"


class TestNormalizeComponents:
    """Test cases for normalize_components function."""
    
    def test_normalize_standard_components(self):
        """Test normalizing standard address components."""
        parsed = {
            'AddressNumber': '123',
            'StreetName': 'Main',
            'StreetNamePostModifier': 'Street',
            'PlaceName': 'Austin',
            'StateName': 'TX',
            'ZipCode': '78701'
        }
        
        result = normalize_components(parsed)
        
        assert result['street_number'] == '123'
        assert result['street_name'] == 'MAIN'
        assert result['street_type'] == 'STREET'
        assert result['city'] == 'AUSTIN'
        assert result['state'] == 'TX'
        assert result['zip_code'] == '78701'
    
    def test_normalize_zip_plus4(self):
        """Test normalizing ZIP+4 code."""
        parsed = {
            'ZipCode': '78701',
            'ZipPlus4': '1234'
        }
        
        result = normalize_components(parsed)
        
        assert result['zip_code'] == '78701-1234'
    
    def test_normalize_unit_components(self):
        """Test normalizing unit components."""
        parsed = {
            'OccupancyType': 'Apartment',
            'OccupancyIdentifier': '456'
        }
        
        result = normalize_components(parsed)
        
        assert result['unit'] == 'APARTMENT 456'
    
    def test_normalize_empty_components(self):
        """Test normalizing empty components."""
        result = normalize_components({})
        
        assert result == {}
    
    def test_normalize_none_components(self):
        """Test normalizing None components."""
        result = normalize_components(None)
        
        assert result == {}


class TestHandleEdgeCases:
    """Test cases for handle_edge_cases function."""
    
    def test_handle_extra_spaces(self):
        """Test handling extra spaces."""
        address = "  123   Main   Street  ,  Austin  ,  TX  78701  "
        result = handle_edge_cases(address)
        
        assert result == "123 MAIN ST, AUSTIN, TX 78701"
    
    def test_handle_street_abbreviations(self):
        """Test handling street type abbreviations."""
        address = "123 Main Avenue, Austin, TX 78701"
        result = handle_edge_cases(address)
        
        assert "AVE" in result
    
    def test_handle_directional_abbreviations(self):
        """Test handling directional abbreviations."""
        address = "123 North Main Street, Austin, TX 78701"
        result = handle_edge_cases(address)
        
        assert "N MAIN" in result
    
    def test_handle_apartment_abbreviations(self):
        """Test handling apartment abbreviations."""
        address = "123 Main St Apartment 456, Austin, TX 78701"
        result = handle_edge_cases(address)
        
        assert "APT 456" in result
    
    def test_handle_po_box_variations(self):
        """Test handling PO Box variations."""
        test_cases = [
            "P.O. Box 123, Austin, TX 78701",
            "Post Office Box 123, Austin, TX 78701",
            "PO Box 123, Austin, TX 78701"
        ]
        
        for address in test_cases:
            result = handle_edge_cases(address)
            assert "PO BOX" in result
    
    def test_handle_empty_address(self):
        """Test handling empty address."""
        result = handle_edge_cases("")
        
        assert result == ""
    
    def test_handle_none_address(self):
        """Test handling None address."""
        result = handle_edge_cases(None)
        
        assert result == ""
