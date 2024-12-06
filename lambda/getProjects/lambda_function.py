import json

from utils.models import Projects
from shared.apiutils import bundle_response


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))
    projects = Projects.scan()
    response = [project.to_dict() for project in projects]
    print("Returning Response: {}".format(json.dumps(response)))
    return bundle_response(200, response)
