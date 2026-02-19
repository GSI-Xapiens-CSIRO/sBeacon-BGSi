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
  value       = aws_dynamodb_table.clinic_jobs.name
  description = "Dynamo clinic jobs table"
}

output "dynamo-clinic-jobs-table-arn" {
  value       = aws_dynamodb_table.clinic_jobs.arn
  description = "Dynamo clinic jobs table"
}
# RBAC Tables Outputs
output "dynamo-roles-table" {
  value       = aws_dynamodb_table.roles.name
  description = "Dynamo roles table for RBAC"
}

output "dynamo-roles-table-arn" {
  value       = aws_dynamodb_table.roles.arn
  description = "Dynamo roles table ARN for RBAC"
}

output "dynamo-permissions-table" {
  value       = aws_dynamodb_table.permissions.name
  description = "Dynamo permissions table for RBAC"
}

output "dynamo-permissions-table-arn" {
  value       = aws_dynamodb_table.permissions.arn
  description = "Dynamo permissions table ARN for RBAC"
}

output "dynamo-role-permissions-table" {
  value       = aws_dynamodb_table.role_permissions.name
  description = "Dynamo role-permissions mapping table for RBAC"
}

output "dynamo-role-permissions-table-arn" {
  value       = aws_dynamodb_table.role_permissions.arn
  description = "Dynamo role-permissions mapping table ARN for RBAC"
}

output "dynamo-user-roles-table" {
  value       = aws_dynamodb_table.user_roles.name
  description = "Dynamo user-roles mapping table for RBAC"
}

output "dynamo-user-roles-table-arn" {
  value       = aws_dynamodb_table.user_roles.arn
  description = "Dynamo user-roles mapping table ARN for RBAC"
}

output "rbac-admin-role-id" {
  value       = random_uuid.admin_role_id.result
  description = "Admin role ID for RBAC system"
  sensitive   = true
}
output "dynamo-clinic-jobs-stream-arn" {
  value       = aws_dynamodb_table.clinic_jobs.stream_arn
  description = "Dynammo clinic jobs table"
}