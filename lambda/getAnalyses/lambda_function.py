import json
from urllib.parse import unquote

from route_analyses import route as route_analyses
from route_analyses_filtering_terms import route as route_analyses_filtering_terms
from route_analyses_id import route as route_analyses_id
from route_analyses_id_g_variants import route as route_analyses_id_g_variants
from shared.apiutils import parse_request, bundle_response
from shared.dynamodb import get_user_quota


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    request_params, errors, status = parse_request(event)
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    user_has_quota = get_user_quota(sub)

    if not user_has_quota:
        return bundle_response(
            403, {"error": "User has exceeded quota", "code": "QUOTA_EXCEEDED"}
        )

    if errors:
        return bundle_response(status, errors)

    if event["resource"] == "/analyses":
        return route_analyses(request_params)

    elif event["resource"] == "/analyses/filtering_terms":
        return route_analyses_filtering_terms(request_params)

    elif event["resource"] == "/analyses/{id}":
        analysis_id = unquote(event["pathParameters"]["id"])
        return route_analyses_id(request_params, analysis_id)

    elif event["resource"] == "/analyses/{id}/g_variants":
        analysis_id = unquote(event["pathParameters"]["id"])
        return route_analyses_id_g_variants(request_params, analysis_id)


if __name__ == "__main__":
    pass
