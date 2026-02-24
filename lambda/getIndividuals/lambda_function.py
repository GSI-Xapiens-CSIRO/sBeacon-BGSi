from shared.apiutils import LambdaRouter, parse_request, bundle_response, require_quota
from shared.cognitoutils import require_permissions

from route_individuals import route as route_individuals
from route_individuals_id import route as route_individuals_id
from route_individuals_id_g_variants import route as route_individuals_id_g_variants
from route_individuals_id_biosamples import route as route_individuals_id_biosamples
from route_individuals_filtering_terms import route as route_individuals_filtering_terms

router = LambdaRouter()


def require_permission_and_quota(event, context):
    """Combined middleware for permission check and quota"""
    require_permissions('sbeacon_query.read')(event, context)
    require_quota(event, context)


@router.attach("/individuals", "post", require_permission_and_quota)
def get_individuals(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    return route_individuals(request_params)


@router.attach("/individuals/filtering_terms", "post", require_permission_and_quota)
def get_individuals_filtering_terms(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    return route_individuals_filtering_terms(request_params)


@router.attach("/individuals/{id}", "post", require_permission_and_quota)
def get_individuals_by_id(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    individual_id = event["pathParameters"]["id"]
    return route_individuals_id(request_params, individual_id)


@router.attach("/individuals/{id}/g_variants", "post", require_permission_and_quota)
def get_individuals_g_variants(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    individual_id = event["pathParameters"]["id"]
    return route_individuals_id_g_variants(request_params, individual_id)


@router.attach("/individuals/{id}/biosamples", "post", require_permission_and_quota)
def get_individuals_biosamples(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    individual_id = event["pathParameters"]["id"]
    return route_individuals_id_biosamples(request_params, individual_id)


def lambda_handler(event, context):
    return router.handle_route(event, context)


if __name__ == "__main__":
    pass
