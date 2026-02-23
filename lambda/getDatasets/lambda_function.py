from shared.apiutils import LambdaRouter, parse_request, bundle_response
from shared.dynamodb import Quota

from route_datasets import route as route_datasets
from route_datasets_id import route as route_datasets_id
from route_datasets_id_g_variants import route as route_datasets_id_g_variants
from route_datasets_id_biosamples import route as route_datasets_id_biosamples
from route_datasets_id_individuals import route as route_datasets_id_individuals
from route_datasets_id_filtering_terms import route as route_datasets_id_filtering_terms

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


@router.attach("/datasets", "get", require_quota)
@router.attach("/datasets", "post", require_quota)
def get_datasets(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    return route_datasets(request_params)


@router.attach("/datasets/{id}", "get", require_quota)
@router.attach("/datasets/{id}", "post", require_quota)
def get_datasets_by_id(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    dataset_id = event["pathParameters"]["id"]
    return route_datasets_id(request_params, dataset_id)


@router.attach("/datasets/{id}/g_variants", "get", require_quota)
@router.attach("/datasets/{id}/g_variants", "post", require_quota)
def get_datasets_g_variants(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    dataset_id = event["pathParameters"]["id"]
    return route_datasets_id_g_variants(request_params, dataset_id)


@router.attach("/datasets/{id}/biosamples", "get", require_quota)
@router.attach("/datasets/{id}/biosamples", "post", require_quota)
def get_datasets_biosamples(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    dataset_id = event["pathParameters"]["id"]
    return route_datasets_id_biosamples(request_params, dataset_id)


@router.attach("/datasets/{id}/individuals", "get", require_quota)
@router.attach("/datasets/{id}/individuals", "post", require_quota)
def get_datasets_individuals(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    dataset_id = event["pathParameters"]["id"]
    return route_datasets_id_individuals(request_params, dataset_id)


@router.attach("/datasets/{id}/filtering_terms", "get", require_quota)
@router.attach("/datasets/{id}/filtering_terms", "post", require_quota)
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
