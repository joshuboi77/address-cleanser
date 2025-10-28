"""
Performance tests for the Address Cleanser tool.
"""

import pytest
import time
import psutil
import os
import tempfile
import pandas as pd
from src.parser import parse_address
from src.validator import validate_address
from src.formatter import create_formatted_address_result


class TestPerformance:
    """Performance benchmark tests."""

    def test_single_address_processing_speed(self):
        """Test processing speed for single addresses."""
        test_address = "123 Main Street, Austin, TX 78701"
        
        # Warm up
        for _ in range(5):
            parse_address(test_address)
        
        # Benchmark
        start_time = time.time()
        iterations = 100
        
        for _ in range(iterations):
            parsed_result = parse_address(test_address)
            normalized = parsed_result.get('parsed', {})
            validation_result = validate_address(normalized)
            create_formatted_address_result(test_address, parsed_result, validation_result)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time_per_address = total_time / iterations
        
        # Should process at least 10 addresses per second
        assert avg_time_per_address < 0.1, f"Too slow: {avg_time_per_address:.3f}s per address"
        
        # Log performance for monitoring
        print(f"Single address processing: {avg_time_per_address:.3f}s per address")
        print(f"Throughput: {1/avg_time_per_address:.1f} addresses/second")

    def test_batch_processing_speed(self):
        """Test processing speed for batch operations."""
        # Create test data
        test_addresses = [
            "123 Main Street, Austin, TX 78701",
            "456 Oak Avenue, Dallas, TX 75201",
            "789 Pine Road, Houston, TX 77001",
            "321 Elm Drive, San Antonio, TX 78201",
            "654 Maple Lane, Fort Worth, TX 76101"
        ] * 20  # 100 addresses total
        
        start_time = time.time()
        
        results = []
        for address in test_addresses:
            parsed_result = parse_address(address)
            normalized = parsed_result.get('parsed', {})
            validation_result = validate_address(normalized)
            result = create_formatted_address_result(address, parsed_result, validation_result)
            results.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time_per_address = total_time / len(test_addresses)
        
        # Should process at least 5 addresses per second in batch
        assert avg_time_per_address < 0.2, f"Too slow: {avg_time_per_address:.3f}s per address"
        
        print(f"Batch processing: {avg_time_per_address:.3f}s per address")
        print(f"Batch throughput: {1/avg_time_per_address:.1f} addresses/second")

    def test_memory_usage_small_batch(self):
        """Test memory usage for small batch processing."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process 100 addresses
        test_addresses = [f"{i} Test Street, Austin, TX 78701" for i in range(100)]
        
        results = []
        for address in test_addresses:
            parsed_result = parse_address(address)
            normalized = parsed_result.get('parsed', {})
            validation_result = validate_address(normalized)
            result = create_formatted_address_result(address, parsed_result, validation_result)
            results.append(result)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Should not use more than 50MB for 100 addresses
        assert memory_increase < 50, f"Too much memory used: {memory_increase:.1f}MB"
        
        print(f"Memory usage for 100 addresses: {memory_increase:.1f}MB")

    def test_memory_usage_large_batch(self):
        """Test memory usage for large batch processing."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process 1000 addresses
        test_addresses = [f"{i} Test Street, Austin, TX 78701" for i in range(1000)]
        
        results = []
        for address in test_addresses:
            parsed_result = parse_address(address)
            normalized = parsed_result.get('parsed', {})
            validation_result = validate_address(normalized)
            result = create_formatted_address_result(address, parsed_result, validation_result)
            results.append(result)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Should not use more than 200MB for 1000 addresses
        assert memory_increase < 200, f"Too much memory used: {memory_increase:.1f}MB"
        
        print(f"Memory usage for 1000 addresses: {memory_increase:.1f}MB")

    def test_csv_io_performance(self):
        """Test CSV I/O performance."""
        # Create test data
        test_addresses = [f"{i} Test Street, Austin, TX 78701" for i in range(100)]
        
        # Create input CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('address\n')
            for addr in test_addresses:
                f.write(f'{addr}\n')
            input_file = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_file = f.name
        
        try:
            # Test CSV processing
            start_time = time.time()
            
            df = pd.read_csv(input_file)
            addresses = df['address'].tolist()
            
            results = []
            for address in addresses:
                parsed_result = parse_address(address)
                normalized = parsed_result.get('parsed', {})
                validation_result = validate_address(normalized)
                result = create_formatted_address_result(address, parsed_result, validation_result)
                results.append(result)
            
            # Convert to DataFrame and save
            csv_data = []
            for result in results:
                row = {
                    'original_address': result['original'],
                    'street_number': result['parsed'].get('street_number', ''),
                    'street_name': result['parsed'].get('street_name', ''),
                    'street_type': result['parsed'].get('street_type', ''),
                    'city': result['parsed'].get('city', ''),
                    'state': result['parsed'].get('state', ''),
                    'zip_code': result['parsed'].get('zip_code', ''),
                    'formatted_address': result['single_line'],
                    'confidence_score': result['confidence'],
                    'validation_status': 'Valid' if result['valid'] else 'Invalid'
                }
                csv_data.append(row)
            
            df_output = pd.DataFrame(csv_data)
            df_output.to_csv(output_file, index=False)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should process 100 addresses in under 10 seconds
            assert total_time < 10, f"CSV processing too slow: {total_time:.2f}s"
            
            print(f"CSV processing time for 100 addresses: {total_time:.2f}s")
            
        finally:
            os.unlink(input_file)
            os.unlink(output_file)

    def test_different_address_types_performance(self):
        """Test performance with different address types."""
        test_cases = [
            "123 Main Street, Austin, TX 78701",  # Standard
            "PO Box 123, Austin, TX 78701",      # PO Box
            "123 Main St Apt 456, Austin, TX 78701",  # Apartment
            "123 North Main Street, Austin, TX 78701",  # With directional
            "123 Main St, Austin TX 78701-1234"  # ZIP+4
        ]
        
        start_time = time.time()
        iterations = 20  # 100 total operations
        
        for _ in range(iterations):
            for address in test_cases:
                parsed_result = parse_address(address)
                normalized = parsed_result.get('parsed', {})
                validation_result = validate_address(normalized)
                create_formatted_address_result(address, parsed_result, validation_result)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time_per_address = total_time / (len(test_cases) * iterations)
        
        # Should handle different types efficiently
        assert avg_time_per_address < 0.1, f"Too slow for mixed types: {avg_time_per_address:.3f}s"
        
        print(f"Mixed address types processing: {avg_time_per_address:.3f}s per address")

    def test_error_handling_performance(self):
        """Test performance when handling invalid addresses."""
        test_addresses = [
            "123 Main Street, Austin, TX 78701",  # Valid
            "Invalid Address",                     # Invalid
            "",                                   # Empty
            "123",                                # Partial
            "123 Main Street, Austin, TX 78701"   # Valid again
        ] * 20  # 100 addresses total
        
        start_time = time.time()
        
        results = []
        for address in test_addresses:
            parsed_result = parse_address(address)
            normalized = parsed_result.get('parsed', {})
            validation_result = validate_address(normalized)
            result = create_formatted_address_result(address, parsed_result, validation_result)
            results.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time_per_address = total_time / len(test_addresses)
        
        # Should handle errors efficiently
        assert avg_time_per_address < 0.15, f"Too slow with errors: {avg_time_per_address:.3f}s"
        
        print(f"Error handling performance: {avg_time_per_address:.3f}s per address")
