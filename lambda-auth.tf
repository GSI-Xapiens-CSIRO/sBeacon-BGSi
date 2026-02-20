#
# Auth Lambda Function
#
module "lambda-auth" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "sbeacon-backend-auth"
  description         = "Backend function to handle authentication."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 512
  timeout             = 60
  source_path         = "${path.module}/lambda/auth"
  attach_policy_jsons = true
  number_of_policy_jsons = 1
  tags                   = var.common-tags

  environment_variables = merge(
     local.sbeacon_variables,
     {
        COGNITO_CLIENT_ID     = var.cognito-client-id

        COGNITO_REGION        = var.region
     }
  )

    policy_jsons = [
      data.aws_iam_policy_document.lambda-basic-execution.json,
    ]

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer,
  ]
}
