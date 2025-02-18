import json

from utils.models import Projects
from shared.apiutils import bundle_response


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))

    query_params = event.get('queryStringParameters', {})
    params = {"limit": 10}
    search_term = None

    if query_params:
        limit = query_params.get("limit", None)
        last_evaluated_key = query_params.get("last_evaluated_key", None)
        search_term = query_params.get("search", None)
        if limit:
            params["limit"] = int(limit)
        if last_evaluated_key:
            params["last_evaluated_key"] = json.loads(last_evaluated_key)

    if search_term:
        search_term = search_term.lower()
        projects = Projects.scan(
            filter_condition=(
                Projects.name_lower.contains(search_term)
                | Projects.description_lower.contains(search_term)
            ),
            **params,
        )
    else:
        projects = Projects.scan(**params)

    data = [project.to_dict() for project in projects]

    last_evaluated_key = (
        json.dumps(projects.last_evaluated_key)
        if projects.last_evaluated_key
        else projects.last_evaluated_key
    )

    print("Returning Response: {}".format(json.dumps({
        "data": data,
        "last_evaluated_key": last_evaluated_key
    })))

    return bundle_response(200, {"success": True, "data": data, "last_evaluated_key": last_evaluated_key})
