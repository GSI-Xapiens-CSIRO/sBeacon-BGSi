#
# API Gateway
#
resource "aws_api_gateway_rest_api" "BeaconApi" {
  name        = "sbeacon-backend-api"
  description = "API That implements the Beacon specification"
  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

#
# Deployment
#
resource "aws_api_gateway_deployment" "BeaconApi" {
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
  # Without enabling create_before_destroy, 
  # API Gateway can return errors such as BadRequestException: 
  # Active stages pointing to this deployment must be moved or deleted on recreation.
  lifecycle {
    create_before_destroy = true
  }
  # https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_deployment#terraform-resources
  # NOTE: The configuration below will satisfy ordering considerations,
  #       but not pick up all future REST API changes. More advanced patterns
  #       are possible, such as using the filesha1() function against the
  #       Terraform configuration file(s) or removing the .id references to
  #       calculate a hash against whole resources. Be aware that using whole
  #       resources will show a difference after the initial implementation.
  #       It will stabilize to only change when resources change afterwards.
  triggers = {
    redeployment = sha1(jsonencode([
      # /configuration
      aws_api_gateway_method.configuration,
      aws_api_gateway_integration.configuration,
      aws_api_gateway_integration_response.configuration,
      aws_api_gateway_method_response.configuration,
      # /info or /
      aws_api_gateway_method.info,
      aws_api_gateway_integration.info,
      aws_api_gateway_integration_response.info,
      aws_api_gateway_method_response.info,
      aws_api_gateway_method.root-get,
      aws_api_gateway_integration.root-get,
      aws_api_gateway_integration_response.root-get,
      aws_api_gateway_method_response.root-get,
      # /map
      aws_api_gateway_method.map,
      aws_api_gateway_integration.map,
      aws_api_gateway_integration_response.map,
      aws_api_gateway_method_response.map,
      # /entry_types
      aws_api_gateway_method.entry_types,
      aws_api_gateway_integration.entry_types,
      aws_api_gateway_integration_response.entry_types,
      aws_api_gateway_method_response.entry_types,
      # /filtering_terms
      aws_api_gateway_method.filtering_terms,
      aws_api_gateway_integration.filtering_terms,
      aws_api_gateway_integration_response.filtering_terms,
      aws_api_gateway_method_response.filtering_terms,
      # /analyses TODO update with other end points
      aws_api_gateway_method.analyses,
      aws_api_gateway_integration.analyses,
      aws_api_gateway_integration_response.analyses,
      aws_api_gateway_method_response.analyses,
      # /g_variants
      aws_api_gateway_method.g_variants,
      aws_api_gateway_method.g_variants_post,
      aws_api_gateway_integration.g_variants,
      aws_api_gateway_integration.g_variants_post,
      aws_api_gateway_integration_response.g_variants,
      aws_api_gateway_integration_response.g_variants_post,
      aws_api_gateway_method_response.g_variants,
      aws_api_gateway_method_response.g_variants_post,
      # /g_variants/{id}
      aws_api_gateway_method.g_variants-id,
      aws_api_gateway_method.g_variants-id_post,
      aws_api_gateway_integration.g_variants-id,
      aws_api_gateway_integration.g_variants-id_post,
      aws_api_gateway_integration_response.g_variants-id,
      aws_api_gateway_integration_response.g_variants-id_post,
      aws_api_gateway_method_response.g_variants-id,
      aws_api_gateway_method_response.g_variants-id_post,
      # /g_variants/{id}/biosamples
      aws_api_gateway_method.g_variants-id-biosamples,
      aws_api_gateway_method.g_variants-id-biosamples_post,
      aws_api_gateway_integration.g_variants-id-biosamples,
      aws_api_gateway_integration.g_variants-id-biosamples_post,
      aws_api_gateway_integration_response.g_variants-id-biosamples,
      aws_api_gateway_integration_response.g_variants-id-biosamples_post,
      aws_api_gateway_method_response.g_variants-id-biosamples,
      aws_api_gateway_method_response.g_variants-id-biosamples_post,
      # /g_variants/{id}/individuals
      aws_api_gateway_method.g_variants-id-individuals,
      aws_api_gateway_method.g_variants-id-individuals_post,
      aws_api_gateway_integration.g_variants-id-individuals,
      aws_api_gateway_integration.g_variants-id-individuals_post,
      aws_api_gateway_integration_response.g_variants-id-individuals,
      aws_api_gateway_integration_response.g_variants-id-individuals_post,
      aws_api_gateway_method_response.g_variants-id-individuals,
      aws_api_gateway_method_response.g_variants-id-individuals_post,
      # /individuals
      aws_api_gateway_method.individuals,
      aws_api_gateway_method.individuals_post,
      aws_api_gateway_integration.individuals,
      aws_api_gateway_integration.individuals_post,
      aws_api_gateway_integration_response.individuals,
      aws_api_gateway_integration_response.individuals_post,
      aws_api_gateway_method_response.individuals,
      aws_api_gateway_method_response.individuals_post,
      # /individuals/filtering_terms
      aws_api_gateway_method.individuals-filtering_terms,
      aws_api_gateway_method.individuals-filtering_terms_post,
      aws_api_gateway_integration.individuals-filtering_terms,
      aws_api_gateway_integration.individuals-filtering_terms_post,
      aws_api_gateway_integration_response.individuals-filtering_terms,
      aws_api_gateway_integration_response.individuals-filtering_terms_post,
      aws_api_gateway_method_response.individuals-filtering_terms,
      aws_api_gateway_method_response.individuals-filtering_terms_post,
      # /individuals/{id}
      aws_api_gateway_method.individuals-id,
      aws_api_gateway_method.individuals-id_post,
      aws_api_gateway_integration.individuals-id,
      aws_api_gateway_integration.individuals-id_post,
      aws_api_gateway_integration_response.individuals-id,
      aws_api_gateway_integration_response.individuals-id_post,
      aws_api_gateway_method_response.individuals-id,
      aws_api_gateway_method_response.individuals-id_post,
      # /individuals/{id}/biosamples
      aws_api_gateway_method.individuals-id-biosamples,
      aws_api_gateway_method.individuals-id-biosamples_post,
      aws_api_gateway_integration.individuals-id-biosamples,
      aws_api_gateway_integration.individuals-id-biosamples_post,
      aws_api_gateway_integration_response.individuals-id-biosamples,
      aws_api_gateway_integration_response.individuals-id-biosamples_post,
      aws_api_gateway_method_response.individuals-id-biosamples,
      aws_api_gateway_method_response.individuals-id-biosamples_post,
      # /individuals/{id}/g_variants
      aws_api_gateway_method.individuals-id-g_variants,
      aws_api_gateway_method.individuals-id-g_variants_post,
      aws_api_gateway_integration.individuals-id-g_variants,
      aws_api_gateway_integration.individuals-id-g_variants_post,
      aws_api_gateway_integration_response.individuals-id-g_variants,
      aws_api_gateway_integration_response.individuals-id-g_variants_post,
      aws_api_gateway_method_response.individuals-id-g_variants,
      aws_api_gateway_method_response.individuals-id-g_variants_post,
      # /biosamples
      aws_api_gateway_method.biosamples,
      aws_api_gateway_method.biosamples_post,
      aws_api_gateway_integration.biosamples,
      aws_api_gateway_integration.biosamples_post,
      aws_api_gateway_integration_response.biosamples,
      aws_api_gateway_integration_response.biosamples_post,
      aws_api_gateway_method_response.biosamples,
      aws_api_gateway_method_response.biosamples_post,
      # /biosamples/filtering_terms
      aws_api_gateway_method.biosamples-filtering_terms,
      aws_api_gateway_method.biosamples-filtering_terms_post,
      aws_api_gateway_integration.biosamples-filtering_terms,
      aws_api_gateway_integration.biosamples-filtering_terms_post,
      aws_api_gateway_integration_response.biosamples-filtering_terms,
      aws_api_gateway_integration_response.biosamples-filtering_terms_post,
      aws_api_gateway_method_response.biosamples-filtering_terms,
      aws_api_gateway_method_response.biosamples-filtering_terms_post,
      # /biosamples/{id}
      aws_api_gateway_method.biosamples-id,
      aws_api_gateway_method.biosamples-id_post,
      aws_api_gateway_integration.biosamples-id,
      aws_api_gateway_integration.biosamples-id_post,
      aws_api_gateway_integration_response.biosamples-id,
      aws_api_gateway_integration_response.biosamples-id_post,
      aws_api_gateway_method_response.biosamples-id,
      aws_api_gateway_method_response.biosamples-id_post,
      # /biosamples/{id}/analyses
      aws_api_gateway_method.biosamples-id-analyses,
      aws_api_gateway_method.biosamples-id-analyses_post,
      aws_api_gateway_integration.biosamples-id-analyses,
      aws_api_gateway_integration.biosamples-id-analyses_post,
      aws_api_gateway_integration_response.biosamples-id-analyses,
      aws_api_gateway_integration_response.biosamples-id-analyses_post,
      aws_api_gateway_method_response.biosamples-id-analyses,
      aws_api_gateway_method_response.biosamples-id-analyses_post,
      # /biosamples/{id}/g_variants
      aws_api_gateway_method.biosamples-id-g_variants,
      aws_api_gateway_method.biosamples-id-g_variants_post,
      aws_api_gateway_integration.biosamples-id-g_variants,
      aws_api_gateway_integration.biosamples-id-g_variants_post,
      aws_api_gateway_integration_response.biosamples-id-g_variants,
      aws_api_gateway_integration_response.biosamples-id-g_variants_post,
      aws_api_gateway_method_response.biosamples-id-g_variants,
      aws_api_gateway_method_response.biosamples-id-g_variants_post,
      # /biosamples/{id}/runs
      aws_api_gateway_method.biosamples-id-runs,
      aws_api_gateway_method.biosamples-id-runs_post,
      aws_api_gateway_integration.biosamples-id-runs,
      aws_api_gateway_integration.biosamples-id-runs_post,
      aws_api_gateway_integration_response.biosamples-id-runs,
      aws_api_gateway_integration_response.biosamples-id-runs_post,
      aws_api_gateway_method_response.biosamples-id-runs,
      aws_api_gateway_method_response.biosamples-id-runs_post,
      # /runs
      aws_api_gateway_method.runs,
      aws_api_gateway_method.runs_post,
      aws_api_gateway_integration.runs,
      aws_api_gateway_integration.runs_post,
      aws_api_gateway_integration_response.runs,
      aws_api_gateway_integration_response.runs_post,
      aws_api_gateway_method_response.runs,
      aws_api_gateway_method_response.runs_post,
      # /runs/filtering_terms
      aws_api_gateway_method.runs-filtering_terms,
      aws_api_gateway_method.runs-filtering_terms_post,
      aws_api_gateway_integration.runs-filtering_terms,
      aws_api_gateway_integration.runs-filtering_terms_post,
      aws_api_gateway_integration_response.runs-filtering_terms,
      aws_api_gateway_integration_response.runs-filtering_terms_post,
      aws_api_gateway_method_response.runs-filtering_terms,
      aws_api_gateway_method_response.runs-filtering_terms_post,
      # /runs/{id}
      aws_api_gateway_method.runs-id,
      aws_api_gateway_method.runs-id_post,
      aws_api_gateway_integration.runs-id,
      aws_api_gateway_integration.runs-id_post,
      aws_api_gateway_integration_response.runs-id,
      aws_api_gateway_integration_response.runs-id_post,
      aws_api_gateway_method_response.runs-id,
      aws_api_gateway_method_response.runs-id_post,
      # /runs/{id}/analyses
      aws_api_gateway_method.runs-id-analyses,
      aws_api_gateway_method.runs-id-analyses_post,
      aws_api_gateway_integration.runs-id-analyses,
      aws_api_gateway_integration.runs-id-analyses_post,
      aws_api_gateway_integration_response.runs-id-analyses,
      aws_api_gateway_integration_response.runs-id-analyses_post,
      aws_api_gateway_method_response.runs-id-analyses,
      aws_api_gateway_method_response.runs-id-analyses_post,
      # /runs/{id}/g_variants
      aws_api_gateway_method.runs-id-g_variants,
      aws_api_gateway_method.runs-id-g_variants_post,
      aws_api_gateway_integration.runs-id-g_variants,
      aws_api_gateway_integration.runs-id-g_variants_post,
      aws_api_gateway_integration_response.runs-id-g_variants,
      aws_api_gateway_integration_response.runs-id-g_variants_post,
      aws_api_gateway_method_response.runs-id-g_variants,
      aws_api_gateway_method_response.runs-id-g_variants_post,
      # /analyses
      aws_api_gateway_method.analyses,
      aws_api_gateway_method.analyses_post,
      aws_api_gateway_integration.analyses,
      aws_api_gateway_integration.analyses_post,
      aws_api_gateway_integration_response.analyses,
      aws_api_gateway_integration_response.analyses_post,
      aws_api_gateway_method_response.analyses,
      aws_api_gateway_method_response.analyses_post,
      # /analyses/{id}
      aws_api_gateway_method.analyses-id,
      aws_api_gateway_method.analyses-id_post,
      aws_api_gateway_integration.analyses-id,
      aws_api_gateway_integration.analyses-id_post,
      aws_api_gateway_integration_response.analyses-id,
      aws_api_gateway_integration_response.analyses-id_post,
      aws_api_gateway_method_response.analyses-id,
      aws_api_gateway_method_response.analyses-id_post,
      # /analyses/{id}/g_variants
      aws_api_gateway_method.analyses-id-g_variants,
      aws_api_gateway_method.analyses-id-g_variants_post,
      aws_api_gateway_integration.analyses-id-g_variants,
      aws_api_gateway_integration.analyses-id-g_variants_post,
      aws_api_gateway_integration_response.analyses-id-g_variants,
      aws_api_gateway_integration_response.analyses-id-g_variants_post,
      aws_api_gateway_method_response.analyses-id-g_variants,
      aws_api_gateway_method_response.analyses-id-g_variants_post,
      # /datasets
      aws_api_gateway_method.datasets,
      aws_api_gateway_method.datasets_post,
      aws_api_gateway_integration.datasets,
      aws_api_gateway_integration.datasets_post,
      aws_api_gateway_integration_response.datasets,
      aws_api_gateway_integration_response.datasets_post,
      aws_api_gateway_method_response.datasets,
      aws_api_gateway_method_response.datasets_post,
      # /datasets/filtering_terms
      aws_api_gateway_method.datasets-filtering_terms,
      aws_api_gateway_method.datasets-filtering_terms_post,
      aws_api_gateway_integration.datasets-filtering_terms,
      aws_api_gateway_integration.datasets-filtering_terms_post,
      aws_api_gateway_integration_response.datasets-filtering_terms,
      aws_api_gateway_integration_response.datasets-filtering_terms_post,
      aws_api_gateway_method_response.datasets-filtering_terms,
      aws_api_gateway_method_response.datasets-filtering_terms_post,
      # /datasets/{id}
      aws_api_gateway_method.datasets-id,
      aws_api_gateway_method.datasets-id_post,
      aws_api_gateway_integration.datasets-id,
      aws_api_gateway_integration.datasets-id_post,
      aws_api_gateway_integration_response.datasets-id,
      aws_api_gateway_integration_response.datasets-id_post,
      aws_api_gateway_method_response.datasets-id,
      aws_api_gateway_method_response.datasets-id_post,
      # /datasets/{id}/filtering_terms
      aws_api_gateway_method.datasets-id-filtering_terms,
      aws_api_gateway_method.datasets-id-filtering_terms_post,
      aws_api_gateway_integration.datasets-id-filtering_terms,
      aws_api_gateway_integration.datasets-id-filtering_terms_post,
      aws_api_gateway_integration_response.datasets-id-filtering_terms,
      aws_api_gateway_integration_response.datasets-id-filtering_terms_post,
      aws_api_gateway_method_response.datasets-id-filtering_terms,
      aws_api_gateway_method_response.datasets-id-filtering_terms_post,
      # /datasets/{id}/individuals
      aws_api_gateway_method.datasets-id-individuals,
      aws_api_gateway_method.datasets-id-individuals_post,
      aws_api_gateway_integration.datasets-id-individuals,
      aws_api_gateway_integration.datasets-id-individuals_post,
      aws_api_gateway_integration_response.datasets-id-individuals,
      aws_api_gateway_integration_response.datasets-id-individuals_post,
      aws_api_gateway_method_response.datasets-id-individuals,
      aws_api_gateway_method_response.datasets-id-individuals_post,
      # /datasets/{id}/g_variants
      aws_api_gateway_method.datasets-id-g_variants,
      aws_api_gateway_method.datasets-id-g_variants_post,
      aws_api_gateway_integration.datasets-id-g_variants,
      aws_api_gateway_integration.datasets-id-g_variants_post,
      aws_api_gateway_integration_response.datasets-id-g_variants,
      aws_api_gateway_integration_response.datasets-id-g_variants_post,
      aws_api_gateway_method_response.datasets-id-g_variants,
      aws_api_gateway_method_response.datasets-id-g_variants_post,
      # /datasets/{id}/biosamples
      aws_api_gateway_method.datasets-id-biosamples,
      aws_api_gateway_method.datasets-id-biosamples_post,
      aws_api_gateway_integration.datasets-id-biosamples,
      aws_api_gateway_integration.datasets-id-biosamples_post,
      aws_api_gateway_integration_response.datasets-id-biosamples,
      aws_api_gateway_integration_response.datasets-id-biosamples_post,
      aws_api_gateway_method_response.datasets-id-biosamples,
      aws_api_gateway_method_response.datasets-id-biosamples_post,
      # admin
      aws_api_gateway_method.admin_proxy,
      aws_api_gateway_integration.admin_proxy,
      aws_api_gateway_integration_response.admin_proxy,
      aws_api_gateway_method_response.admin_proxy,
      # dportal
      aws_api_gateway_method.dportal_proxy,
      aws_api_gateway_integration.dportal_proxy,
      aws_api_gateway_integration_response.dportal_proxy,
      aws_api_gateway_method_response.dportal_proxy,
      # projects
      aws_api_gateway_method.projects,
      aws_api_gateway_integration.projects,
      aws_api_gateway_integration_response.projects,
      aws_api_gateway_method_response.projects,
    ]))
  }
}

resource "aws_api_gateway_stage" "BeaconApi" {
  deployment_id = aws_api_gateway_deployment.BeaconApi.id
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  stage_name    = "prod"
}

resource "aws_api_gateway_method_settings" "BeaconApi" {
  rest_api_id = aws_api_gateway_rest_api.BeaconApi.id
  stage_name  = aws_api_gateway_stage.BeaconApi.stage_name
  method_path = "*/*"

  settings {
    throttling_burst_limit = var.method-queue-size
    throttling_rate_limit  = var.method-max-request-rate
  }
}
