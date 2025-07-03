import json
from urllib.parse import unquote

from shared.apiutils import parse_request, bundle_response
from route_individuals import route as route_individuals
from route_individuals_id import route as route_individuals_id
from route_individuals_id_g_variants import route as route_individuals_id_g_variants
from route_individuals_id_biosamples import route as route_individuals_id_biosamples
from route_individuals_filtering_terms import route as route_individuals_filtering_terms
from shared.dynamodb import Quota


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    request_params, errors, status = parse_request(event)
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]

    try:
        quota = Quota.get(sub)

        if not quota.user_has_quota():
            return bundle_response(
                403, {"error": "User has exceeded quota", "code": "QUOTA_EXCEEDED"}
            )
        else:
            quota.increment_quota()
    except Quota.DoesNotExist:
        return bundle_response(
            403, {"error": "User does not have a quota", "code": "NO_QUOTA"}
        )

    if errors:
        return bundle_response(status, errors)

    if event["resource"] == "/individuals":
        return route_individuals(request_params)

    elif event["resource"] == "/individuals/filtering_terms":
        return route_individuals_filtering_terms(request_params)

    elif event["resource"] == "/individuals/{id}":
        individual_id = unquote(event["pathParameters"]["id"])
        return route_individuals_id(request_params, individual_id)

    elif event["resource"] == "/individuals/{id}/g_variants":
        individual_id = unquote(event["pathParameters"]["id"])
        return route_individuals_id_g_variants(request_params, individual_id)

    elif event["resource"] == "/individuals/{id}/biosamples":
        individual_id = unquote(event["pathParameters"]["id"])
        return route_individuals_id_biosamples(request_params, individual_id)


if __name__ == "__main__":
    pass
