# getProjects Lambda Function

## Overview
Returns the list of projects available in the sBeacon instance. This is a public endpoint.

## Routes

| Path | Method | Middleware |
|------|--------|------------|
| `/projects` | POST | None |

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

Returns list of available projects:

```json
{
  "meta": {
    "beaconId": "org.ga4gh.sbeacon",
    "apiVersion": "v2.0"
  },
  "response": {
    "projects": [
      {
        "id": "project-1",
        "name": "Project 1",
        "description": "Description of project 1",
        "datasets": ["dataset-1", "dataset-2"]
      },
      {
        "id": "project-2",
        "name": "Project 2",
        "description": "Description of project 2",
        "datasets": ["dataset-3"]
      }
    ]
  }
}
```

## Error Handling

- **500 Internal Server Error**: Server-side errors

## Dependencies

- `shared.apiutils`: LambdaRouter, parse_request, bundle_response
