from shared.apiutils import LambdaRouter, parse_request, bundle_response, require_quota
from shared.cognitoutils import require_permissions

from route_datasets import route as route_datasets
from route_datasets_id import route as route_datasets_id
from route_datasets_id_g_variants import route as route_datasets_id_g_variants
from route_datasets_id_biosamples import route as route_datasets_id_biosamples
from route_datasets_id_individuals import route as route_datasets_id_individuals
from route_datasets_id_filtering_terms import route as route_datasets_id_filtering_terms

router = LambdaRouter()


def require_permission_and_quota(event, context):
    """Combined middleware for permission check and quota"""
    require_permissions('sbeacon_query.read')(event, context)
    require_quota(event, context)


@router.attach("/datasets", "post", require_permission_and_quota)
def get_datasets(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    return route_datasets(request_params)


@router.attach("/datasets/{id}", "post", require_permission_and_quota)
def get_datasets_by_id(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    dataset_id = event["pathParameters"]["id"]
    return route_datasets_id(request_params, dataset_id)


@router.attach("/datasets/{id}/g_variants", "post", require_permission_and_quota)
def get_datasets_g_variants(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    dataset_id = event["pathParameters"]["id"]
    return route_datasets_id_g_variants(request_params, dataset_id)


@router.attach("/datasets/{id}/biosamples", "post", require_permission_and_quota)
def get_datasets_biosamples(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    dataset_id = event["pathParameters"]["id"]
    return route_datasets_id_biosamples(request_params, dataset_id)


@router.attach("/datasets/{id}/individuals", "post", require_permission_and_quota)
def get_datasets_individuals(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    dataset_id = event["pathParameters"]["id"]
    return route_datasets_id_individuals(request_params, dataset_id)


@router.attach("/datasets/{id}/filtering_terms", "post", require_permission_and_quota)
def get_datasets_filtering_terms(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    dataset_id = event["pathParameters"]["id"]
    return route_datasets_id_filtering_terms(request_params, dataset_id)


def lambda_handler(event, context):
    return router.handle_route(event, context)


if __name__ == "__main__":
    pass
