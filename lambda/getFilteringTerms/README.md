# getFilteringTerms Lambda Function

## Overview
Returns the list of filtering terms available in the sBeacon instance. This is a public endpoint.

## Routes

| Path | Method | Middleware |
|------|--------|------------|
| `/filtering_terms` | POST | None |

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

Returns list of available filtering terms:

```json
{
  "meta": {
    "beaconId": "org.ga4gh.sbeacon",
    "apiVersion": "v2.0"
  },
  "response": {
    "filteringTerms": [
      {
        "type": "alphanumerical",
        "id": "NCIT:C42331",
        "label": "Age",
        "scopes": ["individual"]
      },
      {
        "type": "ontology",
        "id": "NCIT:C16576",
        "label": "Sex",
        "scopes": ["individual"]
      }
    ]
  }
}
```

## Error Handling

- **500 Internal Server Error**: Server-side errors

## Dependencies

- `shared.apiutils`: LambdaRouter, parse_request, bundle_response
