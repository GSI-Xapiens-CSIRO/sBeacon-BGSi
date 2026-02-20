#
# Auth API
#

# /auth
resource "aws_api_gateway_resource" "auth" {
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  path_part   = "auth"
}

# /auth/login
resource "aws_api_gateway_resource" "auth-login" {
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
  parent_id   = aws_api_gateway_resource.auth.id
  path_part   = "login"
}

resource "aws_api_gateway_method" "auth-login_post" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.auth-login.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "auth-login_post" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.auth-login.id
  http_method             = aws_api_gateway_method.auth-login_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-auth.lambda_function_invoke_arn
}

resource "aws_api_gateway_method_response" "auth-login_post" {
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
  resource_id = aws_api_gateway_resource.auth-login.id
  http_method = aws_api_gateway_method.auth-login_post.http_method
  status_code = "200"
  
  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "auth-login_post" {
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
  resource_id = aws_api_gateway_resource.auth-login.id
  http_method = aws_api_gateway_method.auth-login_post.http_method
  status_code = aws_api_gateway_method_response.auth-login_post.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [
    aws_api_gateway_integration.auth-login_post
  ]
}

resource "aws_lambda_permission" "apigw_lambda_auth" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-auth.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*"
}
