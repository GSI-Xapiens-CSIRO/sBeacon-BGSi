#
# splitQuery Lambda Function
#
resource "aws_lambda_permission" "SNSsplitQuery" {
  statement_id  = "SBeaconBackendAllowSNSsplitQueryInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-splitQuery.lambda_function_arn
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.splitQuery.arn
}


#
# performQuery Lambda Function
#
resource "aws_lambda_permission" "SNSperformQuery" {
  statement_id  = "SBeaconBackendAllowSNSperformQueryInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-performQuery.lambda_function_arn
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.performQuery.arn
}

#
# admin Lambda Function
#
resource "aws_lambda_permission" "SNSemailNotification" {
  statement_id  = "SBeaconBackendAllowSNSemailNotificationInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-logEmailDelivery.lambda_function_arn
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.sesDeliveryLogger.arn
}

#
# updateFiles Lambda Function
#
resource "aws_lambda_permission" "S3updateFiles" {
  statement_id  = "SBeaconBackendAllowS3updateFilesInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-updateFiles.lambda_function_arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.dataportal-bucket.arn
}

#
# deidentifyFiles Lambda Function
#
resource "aws_lambda_permission" "S3deidentifyFiles" {
  statement_id  = "SBeaconBackendAllowS3deidentifyFilesInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-deidentifyFiles.lambda_function_arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.dataportal-bucket.arn
}

#
# cognitoInvokeTrigger Lambda Function
#
resource "aws_lambda_permission" "allow_cognito_invoke_trigger" {
  statement_id  = "AllowExecutionFromCognito"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda-userPasswordResetEmail.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = var.cognito-user-pool-arn
}
