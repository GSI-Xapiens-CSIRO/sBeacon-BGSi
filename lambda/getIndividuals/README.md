# getIndividuals Lambda Function

## Overview
Handles queries for individual (patient/subject) records in the sBeacon API.

## Routes

| Path | Method | Middleware |
|------|--------|------------|
| `/individuals` | POST | Permission + Quota |
| `/individuals/filtering_terms` | POST | Permission + Quota |
| `/individuals/{id}` | POST | Permission + Quota |
| `/individuals/{id}/g_variants` | POST | Permission + Quota |
| `/individuals/{id}/biosamples` | POST | Permission + Quota |

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
