# getEntryTypes Lambda Function

## Overview
Returns the list of entry types supported by the sBeacon instance. This is a public endpoint.

## Routes

| Path | Method | Middleware |
|------|--------|------------|
| `/entry_types` | POST | None |

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

Returns list of supported entry types:

```json
{
  "meta": {
    "beaconId": "org.ga4gh.sbeacon",
    "apiVersion": "v2.0"
  },
  "response": {
    "entryTypes": [
      {
        "id": "genomicVariant",
        "name": "Genomic Variant",
        "ontologyTermForThisType": {
          "id": "SO:0001059",
          "label": "sequence_alteration"
        },
        "partOfSpecification": "Beacon v2.0",
        "defaultSchema": {}
      },
      {
        "id": "biosample",
        "name": "Biosample",
        "ontologyTermForThisType": {
          "id": "OBI:0001479",
          "label": "specimen"
        },
        "partOfSpecification": "Beacon v2.0",
        "defaultSchema": {}
      }
    ]
  }
}
```

## Error Handling

- **500 Internal Server Error**: Server-side errors

## Dependencies

- `shared.apiutils`: LambdaRouter, parse_request, bundle_response
