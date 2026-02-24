from shared.apiutils import LambdaRouter, parse_request, bundle_response, require_quota
from shared.cognitoutils import require_permissions

from route_runs import route as route_runs
from route_runs_id import route as route_runs_id
from route_runs_id_g_variants import route as route_runs_id_g_variants
from route_runs_id_analyses import route as route_runs_id_analyses
from route_runs_filtering_terms import route as route_runs_filtering_terms

router = LambdaRouter()


def require_permission_and_quota(event, context):
    """Combined middleware for permission check and quota"""
    require_permissions('sbeacon_query.read')(event, context)
    require_quota(event, context)


@router.attach("/runs", "post", require_permission_and_quota)
def get_runs(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    return route_runs(request_params)


@router.attach("/runs/filtering_terms", "post", require_permission_and_quota)
def get_runs_filtering_terms(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    return route_runs_filtering_terms(request_params)


@router.attach("/runs/{id}", "post", require_permission_and_quota)
def get_runs_by_id(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    run_id = event["pathParameters"]["id"]
    return route_runs_id(request_params, run_id)


@router.attach("/runs/{id}/g_variants", "post", require_permission_and_quota)
def get_runs_g_variants(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    run_id = event["pathParameters"]["id"]
    return route_runs_id_g_variants(request_params, run_id)


@router.attach("/runs/{id}/analyses", "post", require_permission_and_quota)
def get_runs_analyses(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    run_id = event["pathParameters"]["id"]
    return route_runs_id_analyses(request_params, run_id)


def lambda_handler(event, context):
    return router.handle_route(event, context)


if __name__ == "__main__":
    pass
