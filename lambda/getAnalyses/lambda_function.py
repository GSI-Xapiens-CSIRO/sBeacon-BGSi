import json
from urllib.parse import unquote

from shared.apiutils import LambdaRouter, parse_request, bundle_response, require_quota
from shared.cognitoutils import require_permissions

from route_analyses import route as route_analyses
from route_analyses_filtering_terms import route as route_analyses_filtering_terms
from route_analyses_id import route as route_analyses_id
from route_analyses_id_g_variants import route as route_analyses_id_g_variants

router = LambdaRouter()


def require_permission_and_quota(event, context):
    """Combined middleware for permission check and quota"""
    require_permissions('sbeacon_query.create')(event, context)
    require_quota(event, context)


@router.attach("/analyses", "post", require_permission_and_quota)
def get_analyses(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    return route_analyses(request_params)


@router.attach("/analyses/filtering_terms", "post", require_permission_and_quota)
def get_analyses_filtering_terms(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    return route_analyses_filtering_terms(request_params)


@router.attach("/analyses/{id}", "post", require_permission_and_quota)
def get_analyses_by_id(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    analysis_id = event["pathParameters"]["id"]
    return route_analyses_id(request_params, analysis_id)


@router.attach("/analyses/{id}/g_variants", "post", require_permission_and_quota)
def get_analyses_g_variants(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    analysis_id = event["pathParameters"]["id"]
    return route_analyses_id_g_variants(request_params, analysis_id)


def lambda_handler(event, context):
    return router.handle_route(event, context)


if __name__ == "__main__":
    pass
