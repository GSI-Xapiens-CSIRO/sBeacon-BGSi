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

output "staging-bucket" {
  value       = aws_s3_bucket.staging-bucket.bucket
  description = "S3 bucket for staging."
}

output "data-portal-bucket-arn" {
  value       = aws_s3_bucket.dataportal-bucket.arn
  description = "S3 bucket arn for the data portal."
}
