from shared.apiutils import LambdaRouter, parse_request, bundle_response
from shared.dynamodb import Quota

from route_biosamples import route as route_biosamples
from route_biosamples_id import route as route_biosamples_id
from route_biosamples_id_g_variants import route as route_biosamples_id_g_variants
from route_biosamples_id_analyses import route as route_biosamples_id_analyses
from route_biosamples_id_runs import route as route_biosamples_id_runs
from route_biosamples_filtering_terms import route as route_biosamples_filtering_terms

router = LambdaRouter()


def require_quota(event, context):
    """Middleware to check user quota before processing request"""
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    
    try:
        quota = Quota.get(sub)
        
        if not quota.user_has_quota():
            from shared.apiutils.router import AuthError
            raise AuthError("QUOTA_EXCEEDED", "User has exceeded quota")
        else:
            quota.increment_quota()
    except Quota.DoesNotExist:
        from shared.apiutils.router import AuthError
        raise AuthError("NO_QUOTA", "User does not have a quota")


@router.attach("/biosamples", "get", require_quota)
@router.attach("/biosamples", "post", require_quota)
def get_biosamples(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    return route_biosamples(request_params)


@router.attach("/biosamples/filtering_terms", "get", require_quota)
@router.attach("/biosamples/filtering_terms", "post", require_quota)
def get_biosamples_filtering_terms(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    return route_biosamples_filtering_terms(request_params)


@router.attach("/biosamples/{id}", "get", require_quota)
@router.attach("/biosamples/{id}", "post", require_quota)
def get_biosamples_by_id(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    biosample_id = event["pathParameters"]["id"]
    return route_biosamples_id(request_params, biosample_id)


@router.attach("/biosamples/{id}/g_variants", "get", require_quota)
@router.attach("/biosamples/{id}/g_variants", "post", require_quota)
def get_biosamples_g_variants(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    biosample_id = event["pathParameters"]["id"]
    return route_biosamples_id_g_variants(request_params, biosample_id)


@router.attach("/biosamples/{id}/analyses", "get", require_quota)
@router.attach("/biosamples/{id}/analyses", "post", require_quota)
def get_biosamples_analyses(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    biosample_id = event["pathParameters"]["id"]
    return route_biosamples_id_analyses(request_params, biosample_id)


@router.attach("/biosamples/{id}/runs", "get", require_quota)
@router.attach("/biosamples/{id}/runs", "post", require_quota)
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
