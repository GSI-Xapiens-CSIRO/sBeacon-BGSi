import json
from urllib.parse import unquote

from route_g_variants import route as route_g_variants
from route_g_variants_id import route as route_g_variants_id
from route_g_variants_id_individuals import route as route_g_variants_id_individuals
from route_g_variants_id_biosamples import route as route_g_variants_id_biosamples
from shared.apiutils import parse_request, bundle_response


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    request_params, errors, status = parse_request(event)

    if errors:
        return bundle_response(status, errors)

    if event["resource"] == "/g_variants":
        return route_g_variants(request_params)

    elif event["resource"] == "/g_variants/{id}":
        variant_id = unquote(event["pathParameters"]["id"])
        return route_g_variants_id(request_params, variant_id)

    elif event["resource"] == "/g_variants/{id}/individuals":
        variant_id = unquote(event["pathParameters"]["id"])
        return route_g_variants_id_individuals(request_params, variant_id)

    elif event["resource"] == "/g_variants/{id}/biosamples":
        variant_id = unquote(event["pathParameters"]["id"])
        return route_g_variants_id_biosamples(request_params, variant_id)


if __name__ == "__main__":
    pass
