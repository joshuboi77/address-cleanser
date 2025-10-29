"""
API endpoints for Address Cleanser.

This module defines all REST API endpoints.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from .models import (
    BatchAddressRequest,
    BatchResponse,
    HealthResponse,
    SingleAddressRequest,
    SingleAddressResponse,
    StatsResponse,
    ValidationOptions,
)
from .service import get_address_service

router = APIRouter()


@router.post("/validate", response_model=SingleAddressResponse, status_code=status.HTTP_200_OK)
async def validate_address(request: SingleAddressRequest) -> SingleAddressResponse:
    """
    Validate and format a single address.

    Accepts a JSON payload with an address string and optional flags.
    Returns a standardized address, validation results, and errors if any.
    """
    service = get_address_service()

    options = request.options or ValidationOptions()
    result = service.process_single_address(
        request.address,
        return_parsed=options.return_parsed,
        return_confidence=options.return_confidence,
        return_original=options.return_original,
    )

    return SingleAddressResponse(**result)


@router.post("/batch", response_model=BatchResponse, status_code=status.HTTP_200_OK)
async def batch_process(request: BatchAddressRequest) -> BatchResponse:
    """
    Process multiple addresses in one call.

    Accepts JSON with an array of addresses.
    Returns cleaned results and summary statistics.
    """
    service = get_address_service()

    result = service.process_batch(
        request.addresses,
        return_parsed=request.return_parsed,
        return_confidence=request.return_confidence,
    )

    # Convert results to response models
    response_results = [SingleAddressResponse(**r) for r in result["results"]]

    return BatchResponse(
        results=response_results,
        summary=result["summary"],
    )


@router.post("/batch/upload", status_code=status.HTTP_200_OK)
async def batch_upload(
    file: UploadFile = File(...),
    output_format: str = "json",
    return_parsed: bool = False,
    return_confidence: bool = False,
):
    """
    Process addresses from uploaded CSV or Excel file.

    Accepts multipart/form-data file upload.
    Returns results in the specified format (json, csv, excel).
    """
    import io
    import pandas as pd

    service = get_address_service()

    # Read file content
    contents = await file.read()

    # Determine file type
    if file.filename and file.filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(contents))
    else:
        df = pd.read_csv(io.BytesIO(contents))

    # Find address column (assume first column or column named 'address')
    if "address" in df.columns:
        addresses = df["address"].tolist()
    elif len(df.columns) > 0:
        addresses = df.iloc[:, 0].tolist()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No address column found in file",
        )

    # Process addresses
    result = service.process_batch(
        [str(addr) for addr in addresses if pd.notna(addr)],
        return_parsed=return_parsed,
        return_confidence=return_confidence,
    )

    # Format response based on output_format
    if output_format.lower() == "json":
        return BatchResponse(
            results=[SingleAddressResponse(**r) for r in result["results"]],
            summary=result["summary"],
        )
    elif output_format.lower() == "csv":
        # Create CSV output
        import csv

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["original", "formatted", "valid", "confidence", "errors"],
        )
        writer.writeheader()

        for r in result["results"]:
            writer.writerow(
                {
                    "original": r.get("original", ""),
                    "formatted": r.get("formatted", ""),
                    "valid": str(r.get("valid", {})),
                    "confidence": r.get("confidence", 0.0),
                    "errors": "; ".join(r.get("errors", [])),
                }
            )

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=results.csv"},
        )
    elif output_format.lower() == "excel":
        # Create Excel output
        output = io.BytesIO()
        output_df = pd.DataFrame(
            [
                {
                    "original": r.get("original", ""),
                    "formatted": r.get("formatted", ""),
                    "valid": str(r.get("valid", {})),
                    "confidence": r.get("confidence", 0.0),
                    "errors": "; ".join(r.get("errors", [])),
                }
                for r in result["results"]
            ]
        )
        output_df.to_excel(output, index=False)
        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=results.xlsx"},
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported output format: {output_format}",
        )


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """
    Simple health check to verify the service is running.

    Returns status and version information.
    """
    try:
        from ... import __version__

        version = __version__
    except ImportError:
        version = "1.0.0"

    return HealthResponse(status="healthy", version=version)


@router.get("/stats", response_model=StatsResponse, status_code=status.HTTP_200_OK)
async def get_stats() -> StatsResponse:
    """
    Get processing statistics.

    Returns metrics such as total addresses processed, average confidence scores,
    and recent error counts.
    """
    service = get_address_service()
    stats = service.get_stats()

    return StatsResponse(**stats)
