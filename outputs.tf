output "api_url" {
  value       = aws_api_gateway_deployment.BeaconApi.invoke_url
  description = "URL used to invoke the API."
}

output "api_stage" {
  value       = aws_api_gateway_stage.BeaconApi.stage_name
  description = "API stage."
}

output "data-portal-bucket" {
  value       = aws_s3_bucket.dataportal-bucket.bucket
  description = "S3 bucket for the data portal."
}

output "data-portal-bucket-arn" {
  value       = aws_s3_bucket.dataportal-bucket.arn
  description = "S3 bucket arn for the data portal."
}

output "ses-source-email-arn" {
  value = data.aws_ses_email_identity.ses_source_email.arn
  description = "ARN for the identity from which to send SES emails"
}

output "ses-configuration-set" {
  value = aws_ses_configuration_set.ses_feedback_config.name
}
