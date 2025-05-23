import json
from urllib.parse import unquote

from route_datasets import route as route_datasets
from route_datasets_id import route as route_datasets_id
from route_datasets_id_g_variants import route as route_datasets_id_g_variants
from route_datasets_id_biosamples import route as route_datasets_id_biosamples
from route_datasets_id_individuals import route as route_datasets_id_individuals
from route_datasets_id_filtering_terms import route as route_datasets_id_filtering_terms
from shared.apiutils import bundle_response, parse_request
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

    if event["resource"] == "/datasets":
        return route_datasets(request_params)

    elif event["resource"] == "/datasets/{id}":
        dataset_id = unquote(event["pathParameters"]["id"])
        return route_datasets_id(request_params, dataset_id)

    elif event["resource"] == "/datasets/{id}/g_variants":
        dataset_id = unquote(event["pathParameters"]["id"])
        return route_datasets_id_g_variants(request_params, dataset_id)

    elif event["resource"] == "/datasets/{id}/biosamples":
        dataset_id = unquote(event["pathParameters"]["id"])
        return route_datasets_id_biosamples(request_params, dataset_id)

    elif event["resource"] == "/datasets/{id}/individuals":
        dataset_id = unquote(event["pathParameters"]["id"])
        return route_datasets_id_individuals(request_params, dataset_id)

    elif event["resource"] == "/datasets/{id}/filtering_terms":
        dataset_id = unquote(event["pathParameters"]["id"])
        return route_datasets_id_filtering_terms(request_params, dataset_id)


if __name__ == "__main__":
    pass
