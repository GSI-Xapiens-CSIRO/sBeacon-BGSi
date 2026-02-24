from shared.apiutils import LambdaRouter, parse_request, bundle_response, require_quota
from shared.cognitoutils import require_permissions

from route_biosamples import route as route_biosamples
from route_biosamples_id import route as route_biosamples_id
from route_biosamples_id_g_variants import route as route_biosamples_id_g_variants
from route_biosamples_id_analyses import route as route_biosamples_id_analyses
from route_biosamples_id_runs import route as route_biosamples_id_runs
from route_biosamples_filtering_terms import route as route_biosamples_filtering_terms

router = LambdaRouter()


def require_permission_and_quota(event, context):
    """Combined middleware for permission check and quota"""
    require_permissions('sbeacon_query.read')(event, context)
    require_quota(event, context)


@router.attach("/biosamples", "post", require_permission_and_quota)
def get_biosamples(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    return route_biosamples(request_params)


@router.attach("/biosamples/filtering_terms", "post", require_permission_and_quota)
def get_biosamples_filtering_terms(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    return route_biosamples_filtering_terms(request_params)


@router.attach("/biosamples/{id}", "post", require_permission_and_quota)
def get_biosamples_by_id(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    biosample_id = event["pathParameters"]["id"]
    return route_biosamples_id(request_params, biosample_id)


@router.attach("/biosamples/{id}/g_variants", "post", require_permission_and_quota)
def get_biosamples_g_variants(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    biosample_id = event["pathParameters"]["id"]
    return route_biosamples_id_g_variants(request_params, biosample_id)


@router.attach("/biosamples/{id}/analyses", "post", require_permission_and_quota)
def get_biosamples_analyses(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    biosample_id = event["pathParameters"]["id"]
    return route_biosamples_id_analyses(request_params, biosample_id)


@router.attach("/biosamples/{id}/runs", "post", require_permission_and_quota)
def get_biosamples_runs(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    biosample_id = event["pathParameters"]["id"]
    return route_biosamples_id_runs(request_params, biosample_id)


def lambda_handler(event, context):
    return router.handle_route(event, context)


if __name__ == "__main__":
    pass
