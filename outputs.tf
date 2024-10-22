output "api_url" {
  value       = module.sbeacon-backend.api_url
  description = "URL used to invoke the API."
}

output "api_stage" {
  value       = module.sbeacon-backend.api_stage
  description = "API stage."
}

output "cognito_client_id" {
  value       = module.sbeacon-backend.cognito_client_id
  description = "Cognito client Id for user registration and login."
}

output "cognito_user_pool_id" {
  value       = module.sbeacon-backend.cognito_user_pool_id
  description = "Cognito user pool Id."
}

output "beacon_ui_url" {
  value       = module.seabcon-frontend.cloudfront-url
  description = "URL of the webapp."
}

output "admin_login_command" {
  value       = module.sbeacon-backend.admin_login_command
  description = "Admin Login Command"
}
output "guest_login_command" {
  value       = module.sbeacon-backend.guest_login_command
  description = "Guest Login Command"
}
