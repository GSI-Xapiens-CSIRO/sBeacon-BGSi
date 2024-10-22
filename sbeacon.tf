# TODO userpool must be migrated outside of the beacon module
locals {
  region = var.region
}

module "sbeacon-backend" {
  source                = "./backend"
  region                = local.region
  beacon-id             = "au.bgsi-serverless.beacon"
  beacon-name           = "BGSi Serverless Beacon"
  organisation-id       = "BGSi"
  organisation-name     = "BGSi"
  beacon-enable-auth    = true
  beacon-guest-username = "guest@gmail.com"
  beacon-guest-password = "guest1234pw"
  beacon-admin-username = "admin@gmail.com"
  beacon-admin-password = "admin1234pw"
  common-tags = merge(var.common-tags, {
    "NAME" = "sbeacon-backend"
  })
}

module "seabcon-frontend" {
  source                  = "./frontend/terraform-aws"
  region                  = local.region
  base_range              = 5000
  user_pool_id            = module.sbeacon-backend.cognito_user_pool_id
  identity_pool_id        = module.sbeacon-backend.cognito_identity_pool_id
  user_pool_web_client_id = module.sbeacon-backend.cognito_client_id
  data_portal_bucket      = module.sbeacon-backend.data-portal-bucket
  api_endpoint_sbeacon    = "${module.sbeacon-backend.api_url}${module.sbeacon-backend.api_stage}/"
  common-tags = merge(var.common-tags, {
    "NAME" = "sbeacon-fronted"
  })
}
