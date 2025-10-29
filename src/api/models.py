"""
Pydantic models for API request and response schemas.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ValidationOptions(BaseModel):
    """Options for address validation requests."""

    return_parsed: bool = Field(default=True, description="Include parsed address components")
    return_confidence: bool = Field(
        default=True, description="Include confidence score in response"
    )
    return_original: bool = Field(default=False, description="Include original address in response")


class SingleAddressRequest(BaseModel):
    """Request model for single address validation."""

    address: str = Field(..., description="Address string to validate and format")
    options: Optional[ValidationOptions] = Field(
        default=None, description="Processing options"
    )


class BatchAddressRequest(BaseModel):
    """Request model for batch address processing."""

    addresses: List[str] = Field(..., description="List of address strings to process")
    output_format: Optional[str] = Field(
        default="json", description="Output format: json, csv, excel"
    )
    return_parsed: bool = Field(
        default=False, description="Include parsed components in batch results"
    )
    return_confidence: bool = Field(
        default=False, description="Include confidence scores in batch results"
    )


class ValidationResult(BaseModel):
    """Validation result model."""

    state: bool = Field(..., description="Whether state is valid")
    zip: bool = Field(..., description="Whether ZIP code is valid")
    is_complete: bool = Field(..., description="Whether address is complete")


class SingleAddressResponse(BaseModel):
    """Response model for single address validation."""

    formatted: str = Field(..., description="USPS-formatted address string")
    parsed: Optional[Dict[str, Any]] = Field(
        default=None, description="Parsed address components"
    )
    valid: ValidationResult = Field(..., description="Validation results")
    confidence: Optional[float] = Field(
        default=None, description="Parsing confidence score (0-100)"
    )
    errors: List[str] = Field(default_factory=list, description="List of errors or warnings")
    original: Optional[str] = Field(
        default=None, description="Original address string"
    )


class BatchSummary(BaseModel):
    """Summary statistics for batch processing."""

    total: int = Field(..., description="Total number of addresses processed")
    valid: int = Field(..., description="Number of valid addresses")
    invalid: int = Field(..., description="Number of invalid addresses")
    errors: int = Field(..., description="Number of addresses with errors")


class BatchResponse(BaseModel):
    """Response model for batch address processing."""

    results: List[SingleAddressResponse] = Field(
        ..., description="List of processed address results"
    )
    summary: BatchSummary = Field(..., description="Batch processing summary")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")


class StatsResponse(BaseModel):
    """Response model for statistics endpoint."""

    total_processed: int = Field(..., description="Total addresses processed")
    total_valid: int = Field(..., description="Total valid addresses")
    total_invalid: int = Field(..., description="Total invalid addresses")
    total_errors: int = Field(..., description="Total errors encountered")
    average_confidence: float = Field(..., description="Average confidence score")
    recent_error_count: int = Field(..., description="Recent error count")

