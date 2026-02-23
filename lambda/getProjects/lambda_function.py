import json

from utils.models import Projects
from shared.apiutils import LambdaRouter, bundle_response

router = LambdaRouter()


@router.attach("/projects", "get")
@router.attach("/projects", "post")
def get_projects(event, context):
    query_params = event.get('queryStringParameters', {}) or {}
    params = {"limit": 10}
    search_term = None

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

    return bundle_response(200, {"success": True, "data": data, "last_evaluated_key": last_evaluated_key})


def lambda_handler(event, context):
    return router.handle_route(event, context)
