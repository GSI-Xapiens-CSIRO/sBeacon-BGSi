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
