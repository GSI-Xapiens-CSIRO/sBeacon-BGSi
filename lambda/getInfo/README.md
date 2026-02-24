# getInfo Lambda Function

## Overview
Returns basic information about the sBeacon instance. This is a public endpoint.

## Routes

| Path | Method | Middleware |
|------|--------|------------|
| `/` | POST | None |

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

Returns Beacon info response:

```json
{
  "meta": {
    "beaconId": "org.ga4gh.sbeacon",
    "apiVersion": "v2.0",
    "returnedSchemas": []
  },
  "response": {
    "id": "org.ga4gh.sbeacon",
    "name": "sBeacon",
    "apiVersion": "v2.0",
    "environment": "production",
    "organization": {
      "id": "org.ga4gh",
      "name": "Global Alliance for Genomics and Health"
    },
    "description": "Serverless Beacon implementation",
    "version": "2.0",
    "welcomeUrl": "https://...",
    "alternativeUrl": "https://...",
    "createDateTime": "2020-01-01T00:00:00Z",
    "updateDateTime": "2024-01-01T00:00:00Z"
  }
}
```

## Error Handling

- **500 Internal Server Error**: Server-side errors

## Dependencies

- `shared.apiutils`: LambdaRouter, parse_request, bundle_response
