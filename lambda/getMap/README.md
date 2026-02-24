# getMap Lambda Function

## Overview
Returns the map of available endpoints in the sBeacon API. This is a public endpoint.

## Routes

| Path | Method | Middleware |
|------|--------|------------|
| `/map` | POST | None |

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

Returns map of available API endpoints:

```json
{
  "meta": {
    "beaconId": "org.ga4gh.sbeacon",
    "apiVersion": "v2.0"
  },
  "response": {
    "$schema": "...",
    "endpointSets": {
      "genomicVariant": {
        "entryType": "genomicVariant",
        "rootUrl": "https://api.example.com/g_variants",
        "singleEntryUrl": "https://api.example.com/g_variants/{id}",
        "endpoints": {
          "genomicVariant": "/g_variants",
          "individual": "/g_variants/{id}/individuals",
          "biosample": "/g_variants/{id}/biosamples"
        }
      }
    }
  }
}
```

## Error Handling

- **500 Internal Server Error**: Server-side errors

## Dependencies

- `shared.apiutils`: LambdaRouter, parse_request, bundle_response
