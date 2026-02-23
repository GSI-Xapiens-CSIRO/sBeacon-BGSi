from shared.apiutils import LambdaRouter, parse_request, bundle_response
from shared.dynamodb import Quota

from route_individuals import route as route_individuals
from route_individuals_id import route as route_individuals_id
from route_individuals_id_g_variants import route as route_individuals_id_g_variants
from route_individuals_id_biosamples import route as route_individuals_id_biosamples
from route_individuals_filtering_terms import route as route_individuals_filtering_terms

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


@router.attach("/individuals", "get", require_quota)
@router.attach("/individuals", "post", require_quota)
def get_individuals(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    return route_individuals(request_params)


@router.attach("/individuals/filtering_terms", "get", require_quota)
@router.attach("/individuals/filtering_terms", "post", require_quota)
def get_individuals_filtering_terms(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    return route_individuals_filtering_terms(request_params)


@router.attach("/individuals/{id}", "get", require_quota)
@router.attach("/individuals/{id}", "post", require_quota)
def get_individuals_by_id(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    individual_id = event["pathParameters"]["id"]
    return route_individuals_id(request_params, individual_id)


@router.attach("/individuals/{id}/g_variants", "get", require_quota)
@router.attach("/individuals/{id}/g_variants", "post", require_quota)
def get_individuals_g_variants(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    individual_id = event["pathParameters"]["id"]
    return route_individuals_id_g_variants(request_params, individual_id)


@router.attach("/individuals/{id}/biosamples", "get", require_quota)
@router.attach("/individuals/{id}/biosamples", "post", require_quota)
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
