import json
from urllib.parse import unquote

from route_runs import route as route_runs
from route_runs_id import route as route_runs_id
from route_runs_id_g_variants import route as route_runs_id_g_variants
from route_runs_id_analyses import route as route_runs_id_analyses
from route_runs_filtering_terms import route as route_runs_filtering_terms
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

    if event["resource"] == "/runs":
        return route_runs(request_params)

    elif event["resource"] == "/runs/{id}":
        run_id = unquote(event["pathParameters"]["id"])
        return route_runs_id(request_params, run_id)

    elif event["resource"] == "/runs/{id}/g_variants":
        run_id = unquote(event["pathParameters"]["id"])
        return route_runs_id_g_variants(request_params, run_id)

    elif event["resource"] == "/runs/{id}/analyses":
        run_id = unquote(event["pathParameters"]["id"])
        return route_runs_id_analyses(request_params, run_id)

    elif event["resource"] == "/runs/filtering_terms":
        return route_runs_filtering_terms(request_params)


if __name__ == "__main__":
    pass
