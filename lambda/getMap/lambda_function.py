from shared.apiutils import LambdaRouter, beacon_map, bundle_response

router = LambdaRouter()


@router.attach("/map", "post")
def get_map(event, context):
    response = beacon_map()
    return bundle_response(200, response)


def lambda_handler(event, context):
    return router.handle_route(event, context)
