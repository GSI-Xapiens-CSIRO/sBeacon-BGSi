from shared.apiutils import LambdaRouter, parse_request, bundle_response
from shared.dynamodb import Quota

from route_g_variants import route as route_g_variants
from route_g_variants_id import route as route_g_variants_id
from route_g_variants_id_individuals import route as route_g_variants_id_individuals
from route_g_variants_id_biosamples import route as route_g_variants_id_biosamples

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


@router.attach("/g_variants", "get", require_quota)
@router.attach("/g_variants", "post", require_quota)
def get_g_variants(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    return route_g_variants(request_params)


@router.attach("/g_variants/{id}", "get", require_quota)
@router.attach("/g_variants/{id}", "post", require_quota)
def get_g_variants_by_id(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    variant_id = event["pathParameters"]["id"]
    return route_g_variants_id(request_params, variant_id)


@router.attach("/g_variants/{id}/individuals", "get", require_quota)
@router.attach("/g_variants/{id}/individuals", "post", require_quota)
def get_g_variants_individuals(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    variant_id = event["pathParameters"]["id"]
    return route_g_variants_id_individuals(request_params, variant_id)


@router.attach("/g_variants/{id}/biosamples", "get", require_quota)
@router.attach("/g_variants/{id}/biosamples", "post", require_quota)
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
