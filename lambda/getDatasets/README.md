# getDatasets Lambda Function

## Overview
Handles queries for dataset records in the sBeacon API.

## Routes

| Path | Method | Middleware |
|------|--------|------------|
| `/datasets` | POST | Permission + Quota |
| `/datasets/{id}` | POST | Permission + Quota |
| `/datasets/{id}/g_variants` | POST | Permission + Quota |
| `/datasets/{id}/biosamples` | POST | Permission + Quota |
| `/datasets/{id}/individuals` | POST | Permission + Quota |
| `/datasets/{id}/filtering_terms` | POST | Permission + Quota |

## Authentication & Authorization

- **Permission Required**: `sbeacon_query.read`
- **Quota Check**: Yes - increments user quota on each request
- **Auth Method**: Cognito JWT token via API Gateway authorizer

## Request Format

All endpoints accept POST requests with query parameters in the body:

```json
{
  "meta": {
    "apiVersion": "v2.0"
  },
  "query": {
    "filters": [],
    "requestedGranularity": "record",
    "includeResultsetResponses": "HIT"
  }
}
```

## Response Format

Returns Beacon v2 compliant response:

```json
{
  "meta": {
    "beaconId": "...",
    "apiVersion": "v2.0",
    "returnedGranularity": "record"
  },
  "responseSummary": {
    "exists": true,
    "numTotalResults": 10
  },
  "response": {
    "resultSets": [...]
  }
}
```

## Error Handling

- **403 Forbidden**: Quota exceeded or permission denied
- **400 Bad Request**: Invalid request parameters
- **500 Internal Server Error**: Server-side errors

## Dependencies

- `shared.apiutils`: LambdaRouter, require_quota, parse_request, bundle_response
- `shared.cognitoutils`: require_permissions
- `shared.dynamodb`: Quota tracking
