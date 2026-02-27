#
# authActivity API Function /auth_activity (PUBLIC)
# For logging authentication events from Amplify (login, MFA, password reset)
#
resource "aws_api_gateway_resource" "auth_activity" {
  path_part   = "auth_activity"
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

# POST method - NO AUTHORIZER (public endpoint)
resource "aws_api_gateway_method" "auth_activity_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.auth_activity.id
  http_method   = "POST"
  authorization = "NONE"  # PUBLIC - no JWT required
}

resource "aws_api_gateway_method_response" "auth_activity_post" {
  rest_api_id = aws_api_gateway_method.auth_activity_post.rest_api_id
  resource_id = aws_api_gateway_method.auth_activity_post.resource_id
  http_method = aws_api_gateway_method.auth_activity_post.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration" "auth_activity_post" {
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
  resource_id = aws_api_gateway_resource.auth_activity.id
  http_method = aws_api_gateway_method.auth_activity_post.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-authActivity.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "auth_activity_post" {
  rest_api_id = aws_api_gateway_method.auth_activity_post.rest_api_id
  resource_id = aws_api_gateway_method.auth_activity_post.resource_id
  http_method = aws_api_gateway_method.auth_activity_post.http_method
  status_code = aws_api_gateway_method_response.auth_activity_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.auth_activity_post]
}

# CORS configuration
module "cors-auth_activity" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.auth_activity.id
  allow_headers   = ["Content-Type", "X-Amz-Date"]
}

# Lambda permission for API Gateway to invoke
resource "aws_lambda_permission" "API_auth_activity" {
  statement_id  = "AllowAPIAuthActivityInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-authActivity.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/${aws_api_gateway_method.auth_activity_post.http_method}${aws_api_gateway_resource.auth_activity.path}"
}
