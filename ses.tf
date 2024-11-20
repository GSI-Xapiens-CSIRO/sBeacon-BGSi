data "aws_ses_email_identity" "ses_source_email" {
  email = var.ses-source-email
}


resource "aws_ses_configuration_set" "ses_feedback_config" {
  name = "ses-feedback-config"
}

resource "aws_ses_event_destination" "ses_feedback_event_destination" {
  name                   = "ses-feedback-event-destination"
  configuration_set_name = aws_ses_configuration_set.ses_feedback_config.name
  enabled                = true
  matching_types         = ["bounce", "complaint", "delivery"]

  sns_destination {
    topic_arn = aws_sns_topic.sesDeliveryLogger.arn
  }
}

resource "aws_ses_identity_notification_topic" "bounce" {
  identity                 = data.aws_ses_email_identity.ses_source_email.email
  notification_type        = "Bounce"
  topic_arn                = aws_sns_topic.sesDeliveryLogger.arn
  include_original_headers = true
}

resource "aws_ses_identity_notification_topic" "complaint" {
  identity                 = data.aws_ses_email_identity.ses_source_email.email
  notification_type        = "Complaint"
  topic_arn                = aws_sns_topic.sesDeliveryLogger.arn
  include_original_headers = true
}

resource "aws_ses_identity_notification_topic" "delivery" {
  identity                 = data.aws_ses_email_identity.ses_source_email.email
  notification_type        = "Delivery"
  topic_arn                = aws_sns_topic.sesDeliveryLogger.arn
  include_original_headers = true
}
