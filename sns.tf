resource "aws_sns_topic" "splitQuery" {
  name = "splitQuery"
}

resource "aws_sns_topic_subscription" "splitQuery" {
  topic_arn = aws_sns_topic.splitQuery.arn
  protocol  = "lambda"
  endpoint  = module.lambda-splitQuery.lambda_function_arn
}

resource "aws_sns_topic" "performQuery" {
  name = "performQuery"
}

resource "aws_sns_topic_subscription" "performQuery" {
  topic_arn = aws_sns_topic.performQuery.arn
  protocol  = "lambda"
  endpoint  = module.lambda-performQuery.lambda_function_arn
}

resource "aws_sns_topic" "indexer" {
  name = "indexer"
}

resource "aws_sns_topic_subscription" "indexer" {
  topic_arn = aws_sns_topic.indexer.arn
  protocol  = "lambda"
  endpoint  = module.lambda-indexer.lambda_function_arn
}

resource "aws_sns_topic" "sesDeliveryLogger" {
  name = "sesDeliveryLogger"
}

resource "aws_sns_topic_subscription" "sesDeliveryLogger" {
  topic_arn = aws_sns_topic.sesDeliveryLogger.arn
  protocol  = "lambda"
  endpoint  = module.lambda-logEmailDelivery.lambda_function_arn
}

resource "aws_sns_topic_policy" "sesDeliveryLogger" {
  arn    = aws_sns_topic.sesDeliveryLogger.arn
  policy = data.aws_iam_policy_document.ses-sns-access.json
}
