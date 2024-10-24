import boto3

from utils.router import LambdaRouter, PortalError
from utils.models import Projects, UserProjects

router = LambdaRouter()


@router.attach("/dportal/projects", "get")
def list_my_projects(event, context):

    # projects = UserProjects.scan()
    projects = [1, 2, 3]
    return projects
