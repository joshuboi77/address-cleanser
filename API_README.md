# Address Cleanser REST API

This document describes the REST API for Address Cleanser, which provides endpoints for parsing, validating, and formatting US addresses.

## Quick Start

### Running the API Server

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python api_server.py

# Or using uvicorn directly
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **Base URL**: `http://localhost:8000`
- **Interactive Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### 1. Validate Single Address

**Endpoint**: `POST /api/v1/validate`

**Description**: Validate and format a single address string.

**Request Body**:
```json
{
  "address": "123 Main St Apt 5, Austin, TX 78701",
  "options": {
    "return_parsed": true,
    "return_confidence": true,
    "return_original": false
  }
}
```

**Response**:
```json
{
  "formatted": "123 MAIN ST APT 5, AUSTIN, TX 78701",
  "parsed": {
    "address_number": "123",
    "street_name": "Main",
    "street_type": "St",
    "unit_type": "Apt",
    "unit_number": "5",
    "city": "Austin",
    "state": "TX",
    "zip_code": "78701"
  },
  "valid": {
    "state": true,
    "zip": true,
    "is_complete": true
  },
  "confidence": 92.0,
  "errors": []
}
```

### 2. Batch Processing

**Endpoint**: `POST /api/v1/batch`

**Description**: Process multiple addresses in one request.

**Request Body**:
```json
{
  "addresses": [
    "123 Main St, Austin, TX 78701",
    "456 Oak Ave, Dallas, TX 75201"
  ],
  "return_parsed": false,
  "return_confidence": false
}
```

**Response**:
```json
{
  "results": [
    {
      "formatted": "123 MAIN ST, AUSTIN, TX 78701",
      "valid": {
        "state": true,
        "zip": true,
        "is_complete": true
      },
      "errors": []
    }
  ],
  "summary": {
    "total": 2,
    "valid": 2,
    "invalid": 0,
    "errors": 0
  }
}
```

### 3. Batch File Upload

**Endpoint**: `POST /api/v1/batch/upload`

**Description**: Upload a CSV or Excel file for batch processing.

**Request**:
- Method: `POST`
- Content-Type: `multipart/form-data`
- Parameters:
  - `file`: CSV or Excel file
  - `output_format`: "json", "csv", or "excel" (default: "json")
  - `return_parsed`: boolean (default: false)
  - `return_confidence`: boolean (default: false)

**Example using curl**:
```bash
curl -X POST "http://localhost:8000/api/v1/batch/upload" \
  -F "file=@addresses.csv" \
  -F "output_format=json"
```

### 4. Health Check

**Endpoint**: `GET /api/v1/health`

**Description**: Check if the API is running.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### 5. Statistics

**Endpoint**: `GET /api/v1/stats`

**Description**: Get processing statistics.

**Response**:
```json
{
  "total_processed": 150,
  "total_valid": 135,
  "total_invalid": 15,
  "total_errors": 8,
  "average_confidence": 87.5,
  "recent_error_count": 2
}
```

## Authentication

The API supports optional API key authentication via the `X-API-Key` header.

To enable authentication, set the `API_KEYS` environment variable:

```bash
export API_KEYS="key1,key2,key3"
python api_server.py
```

Then include the header in requests:
```bash
curl -H "X-API-Key: key1" http://localhost:8000/api/v1/validate ...
```

## Rate Limiting

The API includes rate limiting to prevent abuse. Default is 60 requests per minute per IP address.

To configure the rate limit:
```bash
export RATE_LIMIT=120  # requests per minute
python api_server.py
```

Rate limit exceeded responses return `429 Too Many Requests`.

## Error Handling

The API returns standard HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing or invalid API key
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

Error responses include a detail message:
```json
{
  "detail": "Invalid address format"
}
```

## Examples

### Python Example

```python
import requests

# Single address validation
response = requests.post(
    "http://localhost:8000/api/v1/validate",
    json={
        "address": "123 Main St, Austin, TX 78701",
        "options": {
            "return_parsed": True,
            "return_confidence": True
        }
    }
)

result = response.json()
print(result["formatted"])
print(result["confidence"])
```

### JavaScript Example

```javascript
const response = await fetch('http://localhost:8000/api/v1/validate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    address: '123 Main St, Austin, TX 78701',
    options: {
      return_parsed: true,
      return_confidence: true
    }
  })
});

const result = await response.json();
console.log(result.formatted);
```

### cURL Example

```bash
curl -X POST "http://localhost:8000/api/v1/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "address": "123 Main St, Austin, TX 78701",
    "options": {
      "return_parsed": true,
      "return_confidence": true
    }
  }'
```

## API Design Notes

The API design follows the specifications in `NEXT_STEPS.md` Phase 3:

- ✅ RESTful endpoints (`/api/v1/validate`, `/api/v1/batch`)
- ✅ Health check endpoint (`/api/v1/health`)
- ✅ Statistics endpoint (`/api/v1/stats`)
- ✅ Rate limiting middleware
- ✅ Basic authentication support
- ✅ OpenAPI/Swagger documentation (automatic with FastAPI)
- ✅ Comprehensive error handling
- ✅ Multiple output formats (JSON, CSV, Excel)

## Next Steps

Future enhancements as outlined in the roadmap:
- ZIP+4 validation integration
- Duplicate detection
- Caching system
- Streaming responses for large batches
- WebSocket support for real-time processing

