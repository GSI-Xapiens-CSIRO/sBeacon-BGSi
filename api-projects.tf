#
# getProjects API Function /projects
#
resource "aws_api_gateway_resource" "projects" {
  path_part   = "projects"
  parent_id   = aws_api_gateway_rest_api.BeaconApi.root_resource_id
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
}

resource "aws_api_gateway_method" "projects" {
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  resource_id   = aws_api_gateway_resource.projects.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "projects" {
  rest_api_id = aws_api_gateway_method.projects.rest_api_id
  resource_id = aws_api_gateway_method.projects.resource_id
  http_method = aws_api_gateway_method.projects.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# enable CORS
module "cors-projects" {
  source  = "squidfunk/api-gateway-enable-cors/aws"
  version = "0.3.3"

  api_id          = aws_api_gateway_rest_api.BeaconApi.id
  api_resource_id = aws_api_gateway_resource.projects.id
}

# wire up lambda
resource "aws_api_gateway_integration" "projects" {
  rest_api_id             = aws_api_gateway_rest_api.BeaconApi.id
  resource_id             = aws_api_gateway_resource.projects.id
  http_method             = aws_api_gateway_method.projects.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.lambda-getProjects.lambda_function_invoke_arn
}

resource "aws_api_gateway_integration_response" "projects" {
  rest_api_id = aws_api_gateway_method.projects.rest_api_id
  resource_id = aws_api_gateway_method.projects.resource_id
  http_method = aws_api_gateway_method.projects.http_method
  status_code = aws_api_gateway_method_response.projects.status_code

  response_templates = {
    "application/json" = ""
  }

  depends_on = [aws_api_gateway_integration.projects]
}

# permit lambda invokation
resource "aws_lambda_permission" "APIGetProjects" {
  statement_id  = "AllowAPIGetProjectsInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-getProjects.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.BeaconApi.execution_arn}/*/*/${aws_api_gateway_resource.projects.path_part}"
}
