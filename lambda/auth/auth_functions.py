import hmac
import hashlib
import base64
import json
import traceback
import boto3
from shared.utils.lambda_utils import ENV_COGNITO
from shared.apiutils import BeaconError, LambdaRouter

# Ensure these match the environment variables set in Terraform
COGNITO_CLIENT_ID = ENV_COGNITO.COGNITO_CLIENT_ID
# Defaults to ap-southeast-3 if not set
COGNITO_REGION = ENV_COGNITO.COGNITO_REGION

router = LambdaRouter()
cognito_client = boto3.client("cognito-idp", region_name=COGNITO_REGION)


@router.attach("/auth/login", "post")
def login(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        username = body.get("username")
        password = body.get("password")

        if not username or not password:
            raise BeaconError(
                error_code="MissingCredentials",
                error_message="Username and password required.",
            )

        auth_params = {
            "USERNAME": username,
            "PASSWORD": password,
        }

        response = cognito_client.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters=auth_params,
            ClientId=COGNITO_CLIENT_ID,
        )

        # Handle challenge (MFA / NEW_PASSWORD_REQUIRED)
        if "ChallengeName" in response:
            return {
                "challenge": response["ChallengeName"],
                "session": response["Session"],
                "challenge_parameters": response.get("ChallengeParameters", {}),
            }

        result = response["AuthenticationResult"]

        return {
            "access_token": result["AccessToken"],
            "id_token": result["IdToken"],
            "refresh_token": result.get("RefreshToken"),
            "expires_in": result["ExpiresIn"],
            "token_type": result["TokenType"],
        }

    except cognito_client.exceptions.NotAuthorizedException:
        raise BeaconError(
            error_code="InvalidCredentials",
            error_message="Invalid username or password.",
        )

    except cognito_client.exceptions.UserNotConfirmedException:
        raise BeaconError(
            error_code="UserNotConfirmed",
            error_message="User not confirmed.",
        )

    except cognito_client.exceptions.PasswordResetRequiredException:
         raise BeaconError(
            error_code="PasswordResetRequired",
            error_message="Password reset required.",
        )

    except cognito_client.exceptions.UserNotFoundException:
         raise BeaconError(
            error_code="InvalidCredentials",
            error_message="Invalid username or password.",
        )

    except BeaconError as e:
        raise e

    except Exception:
        traceback.print_exc()
        raise BeaconError(
            error_code="LoginFailed",
            error_message="Authentication failed.",
        )
