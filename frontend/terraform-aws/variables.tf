# AWS configuration
variable "common-tags" {
  type        = map(string)
  description = "A set of tags to attach to every created resource."
}

variable "region" {
  type        = string
  description = "Deployment region of the webapp."
}

# Build commands
variable "webapp-dir" {
  type        = string
  description = "Relative path to webapp"
  default     = "../webapp/"
}

variable "install-command" {
  type        = string
  description = "Install command to install requirements"
  default     = "pnpm install"
}

variable "build-command" {
  type        = string
  description = "Build command to build the webapp"
  default     = "./node_modules/.bin/ng build --configuration production --subresource-integrity"
}

variable "build-destination" {
  type        = string
  description = "Path to built source"
  default     = "../webapp/dist/beacon-v2-ui/browser/"
}

# environment.ts content
variable "base_range" {
  type        = number
  description = "Base range for the application."
}

variable "user_pool_id" {
  type        = string
  description = "User pool ID for authentication."
}

variable "identity_pool_id" {
  type        = string
  description = "Identity pool ID for authentication."
}

variable "data_portal_bucket" {
  type        = string
  description = "Bucket name of the data portal."
}

variable "user_pool_web_client_id" {
  type        = string
  description = "User pool web client ID for authentication."
}

variable "api_endpoint_sbeacon" {
  type        = string
  description = "API endpoint for sbeacon."
}
