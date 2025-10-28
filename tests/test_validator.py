"""
Test module for the validator functionality.
"""

import pytest

from src.validator import (
    calculate_confidence_score,
    get_state_abbreviation,
    validate_address,
    validate_address_completeness,
    validate_city,
    validate_state,
    validate_street_number,
    validate_zip_code,
)


class TestValidateZipCode:
    """Test cases for validate_zip_code function."""

    def test_validate_5_digit_zip(self):
        """Test validating 5-digit ZIP code."""
        is_valid, error = validate_zip_code("78701")

        assert is_valid is True
        assert error == ""

    def test_validate_zip_plus4(self):
        """Test validating ZIP+4 code."""
        is_valid, error = validate_zip_code("78701-1234")

        assert is_valid is True
        assert error == ""

    def test_validate_invalid_zip_short(self):
        """Test validating short ZIP code."""
        is_valid, error = validate_zip_code("7870")

        assert is_valid is False
        assert "Invalid ZIP code format" in error

    def test_validate_invalid_zip_long(self):
        """Test validating long ZIP code."""
        is_valid, error = validate_zip_code("78701234")

        assert is_valid is False
        assert "Invalid ZIP code format" in error

    def test_validate_empty_zip(self):
        """Test validating empty ZIP code."""
        is_valid, error = validate_zip_code("")

        assert is_valid is False
        assert error == "ZIP code is missing"

    def test_validate_zip_with_spaces(self):
        """Test validating ZIP code with spaces."""
        is_valid, error = validate_zip_code("787 01")

        assert is_valid is True
        assert error == ""


class TestValidateState:
    """Test cases for validate_state function."""

    def test_validate_state_abbreviation(self):
        """Test validating state abbreviation."""
        is_valid, error = validate_state("TX")

        assert is_valid is True
        assert error == ""

    def test_validate_state_name(self):
        """Test validating state name."""
        is_valid, error = validate_state("Texas")

        assert is_valid is True
        assert error == ""

    def test_validate_dc(self):
        """Test validating DC."""
        is_valid, error = validate_state("DC")

        assert is_valid is True
        assert error == ""

    def test_validate_territory(self):
        """Test validating territory."""
        is_valid, error = validate_state("PR")

        assert is_valid is True
        assert error == ""

    def test_validate_invalid_state(self):
        """Test validating invalid state."""
        is_valid, error = validate_state("XX")

        assert is_valid is False
        assert "Invalid state" in error

    def test_validate_empty_state(self):
        """Test validating empty state."""
        is_valid, error = validate_state("")

        assert is_valid is False
        assert error == "State is missing"


class TestValidateAddressCompleteness:
    """Test cases for validate_address_completeness function."""

    def test_validate_complete_address(self):
        """Test validating complete address."""
        address = {
            "street_number": "123",
            "street_name": "Main St",
            "city": "Austin",
            "state": "TX",
        }

        is_complete, missing = validate_address_completeness(address)

        assert is_complete is True
        assert missing == []

    def test_validate_incomplete_address(self):
        """Test validating incomplete address."""
        address = {"street_number": "123", "city": "Austin"}

        is_complete, missing = validate_address_completeness(address)

        assert is_complete is False
        assert "street_name" in missing
        assert "state" in missing

    def test_validate_po_box_address(self):
        """Test validating PO Box address."""
        address = {"po_box": "123", "city": "Austin", "state": "TX"}

        is_complete, missing = validate_address_completeness(address)

        assert is_complete is True
        assert missing == []

    def test_validate_empty_address(self):
        """Test validating empty address."""
        is_complete, missing = validate_address_completeness({})

        assert is_complete is False
        assert missing == ["street_number", "street_name", "city", "state"]


class TestCalculateConfidenceScore:
    """Test cases for calculate_confidence_score function."""

    def test_calculate_high_confidence(self):
        """Test calculating high confidence score."""
        parsed = {"confidence": 80.0}
        validations = {"zip_valid": True, "state_valid": True, "is_complete": True}

        score = calculate_confidence_score(parsed, validations)

        assert score == 100.0  # 80 + 10 + 10 + 15, capped at 100

    def test_calculate_low_confidence(self):
        """Test calculating low confidence score."""
        parsed = {"confidence": 50.0}
        validations = {"zip_valid": False, "state_valid": False, "is_complete": False}

        score = calculate_confidence_score(parsed, validations)

        assert score == 0.0  # 50 - 20 - 20 - 25, clamped to 0

    def test_calculate_mixed_confidence(self):
        """Test calculating mixed confidence score."""
        parsed = {"confidence": 60.0}
        validations = {"zip_valid": True, "state_valid": False, "is_complete": True}

        score = calculate_confidence_score(parsed, validations)

        assert score == 65.0  # 60 + 10 - 20 + 15


class TestValidateAddress:
    """Test cases for validate_address function."""

    def test_validate_valid_address(self):
        """Test validating a valid address."""
        address = {
            "street_number": "123",
            "street_name": "Main St",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701",
        }

        result = validate_address(address)

        assert result["valid"] is True
        assert result["zip_valid"] is True
        assert result["state_valid"] is True
        assert result["is_complete"] is True
        assert result["confidence"] > 0
        assert result["issues"] == []

    def test_validate_invalid_address(self):
        """Test validating an invalid address."""
        address = {"street_number": "123", "city": "Austin", "state": "XX", "zip_code": "invalid"}

        result = validate_address(address)

        assert result["valid"] is False
        assert result["zip_valid"] is False
        assert result["state_valid"] is False
        assert result["is_complete"] is False
        assert len(result["issues"]) > 0


class TestValidateStreetNumber:
    """Test cases for validate_street_number function."""

    def test_validate_valid_street_number(self):
        """Test validating valid street number."""
        is_valid, error = validate_street_number("123")

        assert is_valid is True
        assert error == ""

    def test_validate_street_number_with_letters(self):
        """Test validating street number with letters."""
        is_valid, error = validate_street_number("123A")

        assert is_valid is True
        assert error == ""

    def test_validate_invalid_street_number(self):
        """Test validating invalid street number."""
        is_valid, error = validate_street_number("ABC")

        assert is_valid is False
        assert "Invalid street number" in error

    def test_validate_empty_street_number(self):
        """Test validating empty street number."""
        is_valid, error = validate_street_number("")

        assert is_valid is False
        assert error == "Street number is missing"


class TestValidateCity:
    """Test cases for validate_city function."""

    def test_validate_valid_city(self):
        """Test validating valid city."""
        is_valid, error = validate_city("Austin")

        assert is_valid is True
        assert error == ""

    def test_validate_city_with_hyphen(self):
        """Test validating city with hyphen."""
        is_valid, error = validate_city("San Antonio")

        assert is_valid is True
        assert error == ""

    def test_validate_city_too_short(self):
        """Test validating city that's too short."""
        is_valid, error = validate_city("A")

        assert is_valid is False
        assert "City name too short" in error

    def test_validate_city_too_long(self):
        """Test validating city that's too long."""
        long_city = "A" * 51
        is_valid, error = validate_city(long_city)

        assert is_valid is False
        assert "City name too long" in error

    def test_validate_city_invalid_characters(self):
        """Test validating city with invalid characters."""
        is_valid, error = validate_city("Austin123")

        assert is_valid is False
        assert "City name contains invalid characters" in error


class TestGetStateAbbreviation:
    """Test cases for get_state_abbreviation function."""

    def test_get_abbreviation_from_abbreviation(self):
        """Test getting abbreviation from abbreviation."""
        result = get_state_abbreviation("TX")

        assert result == "TX"

    def test_get_abbreviation_from_name(self):
        """Test getting abbreviation from state name."""
        result = get_state_abbreviation("Texas")

        assert result == "TX"

    def test_get_abbreviation_invalid(self):
        """Test getting abbreviation from invalid input."""
        result = get_state_abbreviation("XX")

        assert result is None

    def test_get_abbreviation_empty(self):
        """Test getting abbreviation from empty input."""
        result = get_state_abbreviation("")

        assert result is None
