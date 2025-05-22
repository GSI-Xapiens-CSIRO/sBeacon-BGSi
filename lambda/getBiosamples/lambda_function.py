import json
from urllib.parse import unquote

from route_biosamples import route as route_biosamples
from route_biosamples_id import route as route_biosamples_id
from route_biosamples_id_g_variants import route as route_biosamples_id_g_variants
from route_biosamples_id_analyses import route as route_biosamples_id_analyses
from route_biosamples_id_runs import route as route_biosamples_id_runs
from route_biosamples_filtering_terms import route as route_biosamples_filtering_terms
from shared.apiutils import parse_request, bundle_response
from shared.dynamodb import Quota


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    request_params, errors, status = parse_request(event)
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    quota = Quota.get(sub)

    if not quota.user_has_quota():
        return bundle_response(
            403, {"error": "User has exceeded quota", "code": "QUOTA_EXCEEDED"}
        )
    else:
        quota.increment_quota()

    if errors:
        return bundle_response(status, errors)

    if event["resource"] == "/biosamples":
        return route_biosamples(request_params)

    elif event["resource"] == "/biosamples/{id}":
        biosample_id = unquote(event["pathParameters"]["id"])
        return route_biosamples_id(request_params, biosample_id)

    elif event["resource"] == "/biosamples/{id}/g_variants":
        biosample_id = unquote(event["pathParameters"]["id"])
        return route_biosamples_id_g_variants(request_params, biosample_id)

    elif event["resource"] == "/biosamples/{id}/analyses":
        biosample_id = unquote(event["pathParameters"]["id"])
        return route_biosamples_id_analyses(request_params, biosample_id)

    elif event["resource"] == "/biosamples/{id}/runs":
        biosample_id = unquote(event["pathParameters"]["id"])
        return route_biosamples_id_runs(request_params, biosample_id)

    elif event["resource"] == "/biosamples/filtering_terms":
        return route_biosamples_filtering_terms(request_params)


if __name__ == "__main__":
    pass
