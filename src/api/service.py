"""
Service layer for address processing.

This module orchestrates parsing, validation, and formatting operations.
"""

from typing import Any, Dict, List, Optional

from ..formatter import create_formatted_address_result
from ..parser import parse_address
from ..validator import validate_address


class AddressService:
    """Service class for processing addresses."""

    def __init__(self):
        """Initialize the address service."""
        self._stats = {
            "total_processed": 0,
            "total_valid": 0,
            "total_invalid": 0,
            "total_errors": 0,
            "confidence_scores": [],
        }

    def process_single_address(
        self,
        address: str,
        return_parsed: bool = True,
        return_confidence: bool = True,
        return_original: bool = True,
    ) -> Dict[str, Any]:
        """
        Process a single address through parsing, validation, and formatting.

        Args:
            address: Raw address string to process
            return_parsed: Whether to include parsed components in response
            return_confidence: Whether to include confidence score
            return_original: Whether to include original address

        Returns:
            Dictionary containing processed address results
        """
        if not address or not isinstance(address, str):
            self._update_stats(False, 0.0, True)
            return {
                "formatted": "",
                "valid": {"state": False, "zip": False, "is_complete": False},
                "errors": ["Invalid input: empty or non-string address"],
            }

        try:
            # Parse the address
            parsed_result = parse_address(address)
            parsed_components = parsed_result.get("parsed", {})
            confidence = parsed_result.get("confidence", 0.0)

            # Validate the address components
            parsed_dict = parsed_result.get("parsed", {})
            normalized = {}
            if parsed_dict:
                from ..parser import normalize_components

                normalized = normalize_components(parsed_dict)

            validated_result = (
                validate_address(normalized)
                if normalized
                else {"valid": False, "issues": ["No parsed components"]}
            )

            # Format the address
            if normalized and validated_result:
                formatted_result = create_formatted_address_result(
                    address, parsed_result, validated_result
                )
                formatted_address = formatted_result.get("single_line", "")
            else:
                formatted_address = ""

            # Build response
            response = {
                "formatted": formatted_address,
                "valid": {
                    "state": validated_result.get("state_valid", False),
                    "zip": validated_result.get("zip_valid", False),
                    "is_complete": validated_result.get("is_complete", False),
                },
                "errors": validated_result.get("issues", []) or [],
            }

            # Add optional fields
            if return_parsed and parsed_components:
                if not normalized:
                    from ..parser import normalize_components

                    normalized = normalize_components(parsed_components)
                response["parsed"] = normalized

            if return_confidence:
                response["confidence"] = confidence

            if return_original:
                response["original"] = address

            # Update statistics
            is_valid = validated_result.get("valid", False)
            has_error = len(response.get("errors", [])) > 0
            self._update_stats(is_valid, confidence, has_error)

            return response

        except Exception as e:
            self._update_stats(False, 0.0, True)
            return {
                "formatted": "",
                "valid": {"state": False, "zip": False, "is_complete": False},
                "errors": [f"Processing error: {str(e)}"],
            }

    def process_batch(
        self, addresses: List[str], return_parsed: bool = False, return_confidence: bool = False
    ) -> Dict[str, Any]:
        """
        Process multiple addresses in batch.

        Args:
            addresses: List of address strings to process
            return_parsed: Whether to include parsed components
            return_confidence: Whether to include confidence scores

        Returns:
            Dictionary containing batch processing results
        """
        results = []
        summary = {
            "total": len(addresses),
            "valid": 0,
            "invalid": 0,
            "errors": 0,
        }

        for address in addresses:
            result = self.process_single_address(
                address, return_parsed=return_parsed, return_confidence=return_confidence
            )
            results.append(result)

            # Update summary
            is_valid = result.get("valid", {}).get("is_complete", False)
            if is_valid:
                summary["valid"] += 1
            else:
                summary["invalid"] += 1

            if result.get("errors"):
                summary["errors"] += 1

        return {
            "results": results,
            "summary": summary,
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics.

        Returns:
            Dictionary containing statistics
        """
        confidence_scores = self._stats["confidence_scores"]
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        )

        return {
            "total_processed": self._stats["total_processed"],
            "total_valid": self._stats["total_valid"],
            "total_invalid": self._stats["total_invalid"],
            "total_errors": self._stats["total_errors"],
            "average_confidence": round(avg_confidence, 2),
            "recent_error_count": self._stats.get("recent_error_count", 0),
        }

    def _update_stats(self, is_valid: bool, confidence: float, has_error: bool) -> None:
        """Update internal statistics."""
        self._stats["total_processed"] += 1
        if is_valid:
            self._stats["total_valid"] += 1
        else:
            self._stats["total_invalid"] += 1

        if has_error:
            self._stats["total_errors"] += 1

        if confidence > 0:
            self._stats["confidence_scores"].append(confidence)
            # Keep only last 1000 scores to prevent memory issues
            if len(self._stats["confidence_scores"]) > 1000:
                self._stats["confidence_scores"] = self._stats["confidence_scores"][-1000:]


# Global service instance
_address_service = None


def get_address_service() -> AddressService:
    """Get or create the global address service instance."""
    global _address_service
    if _address_service is None:
        _address_service = AddressService()
    return _address_service
