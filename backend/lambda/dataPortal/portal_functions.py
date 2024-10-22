import boto3

from shared.apiutils import BeaconError, LambdaRouter
from utils.models import Projects, UserProjects

dynamodb = boto3.resource("dynamodb")
router = LambdaRouter()


@router.attach("/dataportal/projects", "get")
def list_my_projects(event, context):

    # projects = UserProjects.scan()
    projects = [1, 2, 3]
    return projects
