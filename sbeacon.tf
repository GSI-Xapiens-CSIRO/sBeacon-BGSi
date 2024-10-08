# TODO userpool must be migrated outside of the beacon module
locals {
  region = var.region
}

module "sbeacon-backend" {
  source                      = "./backend"
  region                      = local.region
  beacon-id                   = "au.bgsi-serverless.beacon"
  variants-bucket-prefix      = "sbeacon-"
  metadata-bucket-prefix      = "sbeacon-metadata-"
  lambda-layers-bucket-prefix = "sbeacon-lambda-layers-"
  beacon-name                 = "BGSi Serverless Beacon"
  organisation-id             = "BGSi"
  organisation-name           = "BGSi"
  beacon-enable-auth          = true
  beacon-guest-username       = "guest@gmail.com"
  beacon-guest-password       = "guest1234pw"
  beacon-admin-username       = "admin@gmail.com"
  beacon-admin-password       = "admin1234pw"
}

module "seabcon-frontend" {
  source                  = "./frontend/terraform-aws"
  region                  = local.region
  base_range              = 5000
  user_pool_id            = module.sbeacon-backend.cognito_user_pool_id
  user_pool_web_client_id = module.sbeacon-backend.cognito_client_id
  api_endpoint_sbeacon    = "${module.sbeacon-backend.api_url}${module.sbeacon-backend.api_stage}/"
}
