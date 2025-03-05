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

output "dynamo-project-users-table" {
  value       = aws_dynamodb_table.project_users.name
  description = "Dynamo project users table"
}

output "dynamo-project-users-table-arn" {
  value       = aws_dynamodb_table.project_users.arn
  description = "Dynamo project users table"
}

output "dynamo-clinic-jobs-table" {
  value       = aws_dynamodb_table.clinic-jobs.name
  description = "Dynamo clinic jobs table"
}

output "dynamo-clinic-jobs-table-arn" {
  value       = aws_dynamodb_table.clinic-jobs.arn
  description = "Dynamo clinic jobs table"
}

output "dynamo-clinic-jobs-stream-arn" {
  value       = aws_dynamodb_table.clinic-jobs.stream_arn
  description = "Dynammo clinic jobs table"
}