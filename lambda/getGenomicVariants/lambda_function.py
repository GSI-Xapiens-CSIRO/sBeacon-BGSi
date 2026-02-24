from shared.apiutils import LambdaRouter, parse_request, bundle_response, require_quota
from shared.cognitoutils import require_permissions

from route_g_variants import route as route_g_variants
from route_g_variants_id import route as route_g_variants_id
from route_g_variants_id_individuals import route as route_g_variants_id_individuals
from route_g_variants_id_biosamples import route as route_g_variants_id_biosamples

router = LambdaRouter()


def require_permission_and_quota(event, context):
    """Combined middleware for permission check and quota"""
    require_permissions('sbeacon_query.create')(event, context)
    require_quota(event, context)


@router.attach("/g_variants", "post", require_permission_and_quota)
def get_g_variants(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    return route_g_variants(request_params)


@router.attach("/g_variants/{id}", "post", require_permission_and_quota)
def get_g_variants_by_id(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    variant_id = event["pathParameters"]["id"]
    return route_g_variants_id(request_params, variant_id)


@router.attach("/g_variants/{id}/individuals", "post", require_permission_and_quota)
def get_g_variants_individuals(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    variant_id = event["pathParameters"]["id"]
    return route_g_variants_id_individuals(request_params, variant_id)


@router.attach("/g_variants/{id}/biosamples", "post", require_permission_and_quota)
def get_g_variants_biosamples(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    variant_id = event["pathParameters"]["id"]
    return route_g_variants_id_biosamples(request_params, variant_id)


def lambda_handler(event, context):
    return router.handle_route(event, context)


if __name__ == "__main__":
    pass
