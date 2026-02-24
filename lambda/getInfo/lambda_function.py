from shared.apiutils import (
    LambdaRouter,
    parse_request,
    build_beacon_info_response,
    bundle_response,
)

router = LambdaRouter()


@router.attach("/", "post")
def get_info(event, context):
    request_params, errors, status = parse_request(event)
    if errors:
        return bundle_response(status, errors)
    
    authorised_datasets = []
    response = build_beacon_info_response(authorised_datasets, request_params)
    return bundle_response(200, response)


def lambda_handler(event, context):
    return router.handle_route(event, context)
