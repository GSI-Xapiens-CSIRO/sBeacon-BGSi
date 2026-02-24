# getConfiguration Lambda Function

## Overview
Returns the configuration of the sBeacon instance. This is a public endpoint.

## Routes

| Path | Method | Middleware |
|------|--------|------------|
| `/configuration` | POST | None |

## Authentication & Authorization

- **Permission Required**: None (public endpoint)
- **Quota Check**: No
- **Auth Method**: None required

## Request Format

Accepts POST request (empty body or with minimal Beacon request):

```json
{
  "meta": {
    "apiVersion": "v2.0"
  }
}
```

## Response Format

Returns Beacon configuration response:

```json
{
  "meta": {
    "beaconId": "org.ga4gh.sbeacon",
    "apiVersion": "v2.0"
  },
  "response": {
    "$schema": "...",
    "maturityAttributes": {
      "productionStatus": "PROD"
    },
    "securityAttributes": {
      "defaultGranularity": "record",
      "securityLevels": ["PUBLIC", "REGISTERED", "CONTROLLED"]
    },
    "entryTypes": {
      "genomicVariant": {},
      "biosample": {},
      "individual": {},
      "analysis": {},
      "run": {},
      "dataset": {}
    }
  }
}
```

## Error Handling

- **500 Internal Server Error**: Server-side errors

## Dependencies

- `shared.apiutils`: LambdaRouter, parse_request, bundle_response
