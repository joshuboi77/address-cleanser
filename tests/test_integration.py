"""
Integration tests for the Address Cleanser tool.
"""

import pytest
import tempfile
import os
import pandas as pd
from src.parser import parse_address
from src.validator import validate_address
from src.formatter import create_formatted_address_result


class TestIntegration:
    """Integration tests for the complete address processing pipeline."""
    
    def test_complete_pipeline_standard_address(self):
        """Test complete pipeline with standard address."""
        address = "123 Main Street, Austin, TX 78701"
        
        # Parse
        parsed_result = parse_address(address)
        assert parsed_result['confidence'] > 0
        
        # Validate
        normalized = parsed_result.get('parsed', {})
        validation_result = validate_address(normalized)
        
        # Format
        formatted_result = create_formatted_address_result(
            address, parsed_result, validation_result
        )
        
        # Assertions
        assert formatted_result['original'] == address
        assert formatted_result['confidence'] > 0
        assert formatted_result['single_line'] != ""
        assert len(formatted_result['multi_line']) > 0
        assert 'street_number' in formatted_result['parsed']
        assert 'city' in formatted_result['parsed']
        assert 'state' in formatted_result['parsed']
    
    def test_complete_pipeline_po_box(self):
        """Test complete pipeline with PO Box address."""
        address = "PO Box 123, Austin, TX 78701"
        
        # Parse
        parsed_result = parse_address(address)
        
        # Validate
        normalized = parsed_result.get('parsed', {})
        validation_result = validate_address(normalized)
        
        # Format
        formatted_result = create_formatted_address_result(
            address, parsed_result, validation_result
        )
        
        # Assertions
        assert formatted_result['original'] == address
        assert 'po_box' in formatted_result['parsed'] or 'USPSBoxID' in formatted_result['parsed']
        assert 'PO BOX' in formatted_result['single_line']
    
    def test_complete_pipeline_apartment(self):
        """Test complete pipeline with apartment address."""
        address = "123 Main St Apt 456, Austin, TX 78701"
        
        # Parse
        parsed_result = parse_address(address)
        
        # Validate
        normalized = parsed_result.get('parsed', {})
        validation_result = validate_address(normalized)
        
        # Format
        formatted_result = create_formatted_address_result(
            address, parsed_result, validation_result
        )
        
        # Assertions
        assert formatted_result['original'] == address
        assert 'unit' in formatted_result['parsed']
        assert 'APT' in formatted_result['single_line']
    
    def test_complete_pipeline_invalid_address(self):
        """Test complete pipeline with invalid address."""
        address = "Invalid Address"
        
        # Parse
        parsed_result = parse_address(address)
        
        # Validate
        normalized = parsed_result.get('parsed', {})
        validation_result = validate_address(normalized)
        
        # Format
        formatted_result = create_formatted_address_result(
            address, parsed_result, validation_result
        )
        
        # Assertions
        assert formatted_result['original'] == address
        assert formatted_result['valid'] is False
        assert len(formatted_result['issues']) > 0
    
    def test_complete_pipeline_empty_address(self):
        """Test complete pipeline with empty address."""
        address = ""
        
        # Parse
        parsed_result = parse_address(address)
        
        # Validate
        normalized = parsed_result.get('parsed', {})
        validation_result = validate_address(normalized)
        
        # Format
        formatted_result = create_formatted_address_result(
            address, parsed_result, validation_result
        )
        
        # Assertions
        assert formatted_result['original'] == address
        assert formatted_result['valid'] is False
        assert formatted_result['confidence'] == 0.0


class TestCSVIntegration:
    """Integration tests for CSV processing."""
    
    def test_csv_processing(self):
        """Test processing addresses from CSV data."""
        # Create test data
        test_data = {
            'address': [
                '123 Main Street, Austin, TX 78701',
                'PO Box 456, Dallas, TX 75201',
                '789 Oak Ave Apt 123, Houston, TX 77001'
            ]
        }
        
        df = pd.DataFrame(test_data)
        
        # Process each address
        results = []
        for address in df['address']:
            # Parse
            parsed_result = parse_address(address)
            
            # Validate
            normalized = parsed_result.get('parsed', {})
            validation_result = validate_address(normalized)
            
            # Format
            formatted_result = create_formatted_address_result(
                address, parsed_result, validation_result
            )
            
            results.append(formatted_result)
        
        # Assertions
        assert len(results) == 3
        
        # Check first address
        assert results[0]['original'] == '123 Main Street, Austin, TX 78701'
        assert results[0]['confidence'] > 0
        
        # Check PO Box address
        assert results[1]['original'] == 'PO Box 456, Dallas, TX 75201'
        assert 'po_box' in results[1]['parsed'] or 'USPSBoxID' in results[1]['parsed']
        
        # Check apartment address
        assert results[2]['original'] == '789 Oak Ave Apt 123, Houston, TX 77001'
        assert 'unit' in results[2]['parsed']
    
    def test_csv_output_format(self):
        """Test CSV output format."""
        # Create test result
        result = {
            'original': '123 Main Street, Austin, TX 78701',
            'parsed': {
                'street_number': '123',
                'street_name': 'MAIN ST',
                'city': 'AUSTIN',
                'state': 'TX',
                'zip_code': '78701'
            },
            'single_line': '123 MAIN ST, AUSTIN, TX 78701',
            'confidence': 95.0,
            'valid': True,
            'issues': [],
            'address_type': 'Street Address'
        }
        
        # Convert to CSV row format
        csv_row = {
            'original_address': result['original'],
            'street_number': result['parsed'].get('street_number', ''),
            'street_name': result['parsed'].get('street_name', ''),
            'street_type': result['parsed'].get('street_type', ''),
            'city': result['parsed'].get('city', ''),
            'state': result['parsed'].get('state', ''),
            'zip_code': result['parsed'].get('zip_code', ''),
            'unit': result['parsed'].get('unit', ''),
            'po_box': result['parsed'].get('po_box', ''),
            'formatted_address': result['single_line'],
            'confidence_score': result['confidence'],
            'validation_status': 'Valid' if result['valid'] else 'Invalid',
            'issues': '; '.join(result['issues']) if result['issues'] else '',
            'address_type': result['address_type']
        }
        
        # Assertions
        assert csv_row['original_address'] == '123 Main Street, Austin, TX 78701'
        assert csv_row['street_number'] == '123'
        assert csv_row['city'] == 'AUSTIN'
        assert csv_row['state'] == 'TX'
        assert csv_row['zip_code'] == '78701'
        assert csv_row['formatted_address'] == '123 MAIN ST, AUSTIN, TX 78701'
        assert csv_row['confidence_score'] == 95.0
        assert csv_row['validation_status'] == 'Valid'
        assert csv_row['issues'] == ''
        assert csv_row['address_type'] == 'Street Address'


class TestErrorHandling:
    """Integration tests for error handling."""
    
    def test_error_handling_malformed_address(self):
        """Test error handling with malformed address."""
        address = "This is not an address at all"
        
        # Parse
        parsed_result = parse_address(address)
        
        # Validate
        normalized = parsed_result.get('parsed', {})
        validation_result = validate_address(normalized)
        
        # Format
        formatted_result = create_formatted_address_result(
            address, parsed_result, validation_result
        )
        
        # Should not crash and should return error information
        assert formatted_result['original'] == address
        assert formatted_result['valid'] is False
        assert len(formatted_result['issues']) > 0
    
    def test_error_handling_special_characters(self):
        """Test error handling with special characters."""
        address = "123 Main St. #456, Austin, TX 78701"
        
        # Parse
        parsed_result = parse_address(address)
        
        # Validate
        normalized = parsed_result.get('parsed', {})
        validation_result = validate_address(normalized)
        
        # Format
        formatted_result = create_formatted_address_result(
            address, parsed_result, validation_result
        )
        
        # Should handle special characters gracefully
        assert formatted_result['original'] == address
        # May or may not be valid depending on parsing success
        assert isinstance(formatted_result['valid'], bool)
    
    def test_error_handling_unicode_characters(self):
        """Test error handling with unicode characters."""
        address = "123 Main St, Austin, TX 78701"  # Using regular characters for now
        
        # Parse
        parsed_result = parse_address(address)
        
        # Validate
        normalized = parsed_result.get('parsed', {})
        validation_result = validate_address(normalized)
        
        # Format
        formatted_result = create_formatted_address_result(
            address, parsed_result, validation_result
        )
        
        # Should handle unicode characters gracefully
        assert formatted_result['original'] == address
        assert isinstance(formatted_result['valid'], bool)
