output "api_url" {
  value       = "https://${aws_cloudfront_distribution.api_distribution.domain_name}/${aws_api_gateway_stage.BeaconApi.stage_name}/"
  description = "URL used to invoke the API."
}

output "data-portal-bucket" {
  value       = aws_s3_bucket.dataportal-bucket.bucket
  description = "S3 bucket for the data portal."
}

output "data-portal-bucket-arn" {
  value       = aws_s3_bucket.dataportal-bucket.arn
  description = "S3 bucket arn for the data portal."
}
