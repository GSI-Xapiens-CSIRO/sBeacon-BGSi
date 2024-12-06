provider "aws" {
  region = var.region
}

data "aws_caller_identity" "this" {}

# DOCS
# Lambda memory - https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-common.html
#                 https://stackoverflow.com/questions/66522916/aws-lambda-memory-vs-cpu-configuration
#
locals {
  # TODO use the following organisation to refactor the IAM policy assignment
  # this makes the code simpler
  # sbeacon info variables
  sbeacon_variables = {
    # beacon variables
    BEACON_API_VERSION         = var.beacon-api-version
    BEACON_ID                  = var.beacon-id
    BEACON_NAME                = var.beacon-name
    BEACON_ENVIRONMENT         = var.beacon-environment
    BEACON_DESCRIPTION         = var.beacon-description
    BEACON_VERSION             = var.beacon-version
    BEACON_WELCOME_URL         = var.beacon-welcome-url
    BEACON_ALTERNATIVE_URL     = var.beacon-alternative-url
    BEACON_CREATE_DATETIME     = var.beacon-create-datetime
    BEACON_UPDATE_DATETIME     = var.beacon-update-datetime
    BEACON_HANDOVERS           = var.beacon-handovers
    BEACON_DOCUMENTATION_URL   = var.beacon-documentation-url
    BEACON_DEFAULT_GRANULARITY = var.beacon-default-granularity
    BEACON_URI                 = var.beacon-uri
    # organisation variables
    BEACON_ORG_ID          = var.organisation-id
    BEACON_ORG_NAME        = var.organisation-name
    BEACON_ORG_DESCRIPTION = var.beacon-org-description
    BEACON_ORG_ADDRESS     = var.beacon-org-address
    BEACON_ORG_WELCOME_URL = var.beacon-org-welcome-url
    BEACON_ORG_CONTACT_URL = var.beacon-org-contact-url
    BEACON_ORG_LOGO_URL    = var.beacon-org-logo-url
    # beacon service variables
    BEACON_SERVICE_TYPE_GROUP    = var.beacon-service-type-group
    BEACON_SERVICE_TYPE_ARTIFACT = var.beacon-service-type-artifact
    BEACON_SERVICE_TYPE_VERSION  = var.beacon-service-type-version
    # configurations
    CONFIG_MAX_VARIANT_SEARCH_BASE_RANGE = var.config-max-variant-search-base-range
    # sbeacon cloudfront url
    BEACON_UI_URL = var.beacon-ui-url
    # ses variables
    SES_SOURCE_EMAIL = var.ses-source-email
  }
  # athena related variables
  athena_variables = {
    ATHENA_WORKGROUP               = aws_athena_workgroup.sbeacon-workgroup.name
    ATHENA_METADATA_DATABASE       = aws_glue_catalog_database.metadata-database.name
    ATHENA_METADATA_BUCKET         = aws_s3_bucket.metadata-bucket.bucket
    ATHENA_DATASETS_TABLE          = aws_glue_catalog_table.sbeacon-datasets.name
    ATHENA_DATASETS_CACHE_TABLE    = aws_glue_catalog_table.sbeacon-datasets-cache.name
    ATHENA_INDIVIDUALS_TABLE       = aws_glue_catalog_table.sbeacon-individuals.name
    ATHENA_INDIVIDUALS_CACHE_TABLE = aws_glue_catalog_table.sbeacon-individuals-cache.name
    ATHENA_BIOSAMPLES_TABLE        = aws_glue_catalog_table.sbeacon-biosamples.name
    ATHENA_BIOSAMPLES_CACHE_TABLE  = aws_glue_catalog_table.sbeacon-biosamples-cache.name
    ATHENA_RUNS_TABLE              = aws_glue_catalog_table.sbeacon-runs.name
    ATHENA_RUNS_CACHE_TABLE        = aws_glue_catalog_table.sbeacon-runs-cache.name
    ATHENA_ANALYSES_TABLE          = aws_glue_catalog_table.sbeacon-analyses.name
    ATHENA_ANALYSES_CACHE_TABLE    = aws_glue_catalog_table.sbeacon-analyses-cache.name
    ATHENA_TERMS_TABLE             = aws_cloudformation_stack.sbeacon_terms_stack.parameters.TableName
    ATHENA_TERMS_INDEX_TABLE       = aws_cloudformation_stack.sbeacon_terms_index_stack.parameters.TableName
    ATHENA_TERMS_CACHE_TABLE       = aws_glue_catalog_table.sbeacon-terms-cache.name
    ATHENA_RELATIONS_TABLE         = aws_glue_catalog_table.sbeacon-relations.name
  }
  # dynamodb variables
  dynamodb_variables = {
    DYNAMO_ONTOLOGIES_TABLE  = aws_dynamodb_table.ontologies.name
    DYNAMO_ANSCESTORS_TABLE  = aws_dynamodb_table.anscestor_terms.name
    DYNAMO_DESCENDANTS_TABLE = aws_dynamodb_table.descendant_terms.name
    DYNAMO_PROJECT_USERS_TABLE = aws_dynamodb_table.project_users.name
    DYNAMO_PROJECT_USERS_UID_INDEX = local.project_users_uid_index
  }
  # layers
  binaries_layer         = "${aws_lambda_layer_version.binaries_layer.layer_arn}:${aws_lambda_layer_version.binaries_layer.version}"
  python_libraries_layer = module.python_libraries_layer.lambda_layer_arn
  python_modules_layer   = module.python_modules_layer.lambda_layer_arn
}

#
# submitDataset Lambda Function
#
module "lambda-submitDataset" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "sbeacon-backend-submitDataset"
  description         = "Creates or updates a dataset and triggers summariseVcf."
  handler             = "lambda_function.lambda_handler"
  runtime             = "python3.12"
  architectures       = ["x86_64"]
  memory_size         = 1769
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-submitDataset.json,
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json,
    data.aws_iam_policy_document.dynamodb-onto-write-access.json
  ]
  number_of_policy_jsons = 4
  source_path            = "${path.module}/lambda/submitDataset"
  tags                   = var.common-tags

  environment_variables = merge(
    {
      HTS_S3_HOST = "s3.${var.region}.amazonaws.com"
    },
    local.sbeacon_variables,
    local.athena_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.binaries_layer,
    local.python_modules_layer
  ]
}

#
# getInfo Lambda Function
#
module "lambda-getInfo" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "sbeacon-backend-getInfo"
  description   = "Returns basic information about the beacon and the datasets."
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  memory_size   = 1769
  timeout       = 60
  # attach_policy_json = false
  # policy_json        = data.aws_iam_policy_document.lambda-getInfo.json
  source_path = "${path.module}/lambda/getInfo"
  tags        = var.common-tags

  environment_variables = merge(
    local.sbeacon_variables,
    local.athena_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getConfiguration Lambda Function
#
module "lambda-getConfiguration" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "sbeacon-backend-getConfiguration"
  description   = "Get the beacon configuration."
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"
  memory_size   = 1769
  timeout       = 60
  source_path   = "${path.module}/lambda/getConfiguration"

  tags = var.common-tags

  environment_variables = merge(
    local.sbeacon_variables,
    local.athena_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getMap Lambda Function
#
module "lambda-getMap" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "sbeacon-backend-getMap"
  description   = "Get the beacon map."
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"
  memory_size   = 1769
  timeout       = 60
  source_path   = "${path.module}/lambda/getMap"

  tags = var.common-tags

  environment_variables = merge(
    local.sbeacon_variables,
    local.athena_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getEntryTypes Lambda Function
#
module "lambda-getEntryTypes" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "sbeacon-backend-getEntryTypes"
  description   = "Get the beacon map."
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"
  memory_size   = 1769
  timeout       = 60
  source_path   = "${path.module}/lambda/getEntryTypes"

  tags = var.common-tags

  environment_variables = merge(
    local.sbeacon_variables,
    local.athena_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getFilteringTerms Lambda Function
#
module "lambda-getFilteringTerms" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "sbeacon-backend-getFilteringTerms"
  description         = "Get the beacon map."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 1769
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json,
  ]
  number_of_policy_jsons = 2
  source_path            = "${path.module}/lambda/getFilteringTerms"

  tags = var.common-tags

  environment_variables = merge(
    local.sbeacon_variables,
    local.athena_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getAnalyses Lambda Function
#
module "lambda-getAnalyses" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "sbeacon-backend-getAnalyses"
  description         = "Get the beacon map."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 1769
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-getAnalyses.json,
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json
  ]
  number_of_policy_jsons = 3
  source_path            = "${path.module}/lambda/getAnalyses"

  tags = var.common-tags

  environment_variables = merge(
    {
      SPLIT_QUERY_LAMBDA    = module.lambda-splitQuery.lambda_function_name,
      SPLIT_QUERY_TOPIC_ARN = aws_sns_topic.splitQuery.arn
    },
    local.athena_variables,
    local.sbeacon_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getGenomicVariants Lambda Function
#
module "lambda-getGenomicVariants" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "sbeacon-backend-getGenomicVariants"
  description         = "Get the variants."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 1769
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-getGenomicVariants.json,
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json
  ]
  number_of_policy_jsons = 3
  source_path            = "${path.module}/lambda/getGenomicVariants"

  tags = var.common-tags

  environment_variables = merge(
    {
      SPLIT_QUERY_LAMBDA    = module.lambda-splitQuery.lambda_function_name,
      SPLIT_QUERY_TOPIC_ARN = aws_sns_topic.splitQuery.arn
    },
    local.athena_variables,
    local.sbeacon_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getIndividuals Lambda Function
#
module "lambda-getIndividuals" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "sbeacon-backend-getIndividuals"
  description         = "Get the individuals."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 1769
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-getIndividuals.json,
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json
  ]
  number_of_policy_jsons = 3
  source_path            = "${path.module}/lambda/getIndividuals"

  tags = var.common-tags

  environment_variables = merge(
    {
      SPLIT_QUERY_LAMBDA    = module.lambda-splitQuery.lambda_function_name,
      SPLIT_QUERY_TOPIC_ARN = aws_sns_topic.splitQuery.arn
    },
    local.athena_variables,
    local.sbeacon_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getBiosamples Lambda Function
#
module "lambda-getBiosamples" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "sbeacon-backend-getBiosamples"
  description         = "Get the biosamples."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 1769
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-getBiosamples.json,
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json
  ]
  number_of_policy_jsons = 3
  source_path            = "${path.module}/lambda/getBiosamples"

  tags = var.common-tags

  environment_variables = merge(
    {
      SPLIT_QUERY_LAMBDA    = module.lambda-splitQuery.lambda_function_name,
      SPLIT_QUERY_TOPIC_ARN = aws_sns_topic.splitQuery.arn
    },
    local.athena_variables,
    local.sbeacon_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getDatasets Lambda Function
#
module "lambda-getDatasets" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "sbeacon-backend-getDatasets"
  description         = "Get the datasets."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 1769
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-getDatasets.json,
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json
  ]
  number_of_policy_jsons = 3
  source_path            = "${path.module}/lambda/getDatasets"

  tags = var.common-tags

  environment_variables = merge(
    {
      SPLIT_QUERY_LAMBDA    = module.lambda-splitQuery.lambda_function_name,
      SPLIT_QUERY_TOPIC_ARN = aws_sns_topic.splitQuery.arn
    },
    local.athena_variables,
    local.sbeacon_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# getRuns Lambda Function
#
module "lambda-getRuns" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "sbeacon-backend-getRuns"
  description         = "Get the runs."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 1769
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-getRuns.json,
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json
  ]
  number_of_policy_jsons = 3
  source_path            = "${path.module}/lambda/getRuns"

  tags = var.common-tags

  environment_variables = merge(
    {
      SPLIT_QUERY_LAMBDA    = module.lambda-splitQuery.lambda_function_name,
      SPLIT_QUERY_TOPIC_ARN = aws_sns_topic.splitQuery.arn
    },
    local.athena_variables,
    local.sbeacon_variables,
    local.dynamodb_variables
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# splitQuery Lambda Function
#
module "lambda-splitQuery" {
  source = "terraform-aws-modules/lambda/aws"

  function_name      = "sbeacon-backend-splitQuery"
  description        = "Splits a dataset into smaller slices of VCFs and invokes performQuery on each."
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.12"
  memory_size        = 1769
  timeout            = 30
  attach_policy_json = true
  policy_json        = data.aws_iam_policy_document.lambda-splitQuery.json
  source_path        = "${path.module}/lambda/splitQuery"
  tags               = var.common-tags

  environment_variables = {
    PERFORM_QUERY_LAMBDA    = module.lambda-performQuery.lambda_function_name,
    PERFORM_QUERY_TOPIC_ARN = aws_sns_topic.performQuery.arn
  }

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# performQuery Lambda Function
#
module "lambda-performQuery" {
  source = "terraform-aws-modules/lambda/aws"

  function_name          = "sbeacon-backend-performQuery"
  description            = "Queries a slice of a vcf for a specified variant."
  handler                = "lambda_function.lambda_handler"
  runtime                = "python3.12"
  memory_size            = 1769
  timeout                = 10
  ephemeral_storage_size = 1024
  attach_policy_json     = true
  policy_json            = data.aws_iam_policy_document.lambda-performQuery.json
  source_path            = "${path.module}/lambda/performQuery"
  tags                   = var.common-tags

  layers = [
    local.binaries_layer,
    local.python_libraries_layer,
    local.python_modules_layer
  ]

  environment_variables = merge({
    HTS_S3_HOST     = "s3.${var.region}.amazonaws.com"
    VARIANTS_BUCKET = aws_s3_bucket.variants-bucket.bucket
    },
    local.sbeacon_variables,
  local.dynamodb_variables)
}

#
# indexer Lambda Function
#
module "lambda-indexer" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "sbeacon-backend-indexer"
  description         = "Run the indexing tasks."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 1769
  timeout             = 600
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.athena-full-access.json,
    data.aws_iam_policy_document.dynamodb-onto-access.json,
    data.aws_iam_policy_document.dynamodb-onto-write-access.json
  ]
  number_of_policy_jsons = 3
  source_path            = "${path.module}/lambda/indexer"

  tags = var.common-tags

  environment_variables = merge(
    local.dynamodb_variables,
    local.sbeacon_variables,
    local.athena_variables,
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# admin Lambda Function
#
module "lambda-admin" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "sbeacon-backend-admin"
  description         = "Run the admin tasks."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 512
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.admin-lambda-access.json
  ]
  number_of_policy_jsons = 1
  source_path            = "${path.module}/lambda/admin"

  tags = var.common-tags

  environment_variables = merge(
    local.sbeacon_variables,
    { COGNITO_USER_POOL_ID = var.cognito-user-pool-id },
    { COGNITO_ADMIN_GROUP_NAME = var.cognito-admin-group-name },
    { SES_SOURCE_EMAIL = var.ses-source-email },
    { SES_CONFIG_SET_NAME = aws_ses_configuration_set.ses_feedback_config.name },
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer
  ]
}

#
# updateFiles Lambda Function
#
module "lambda-updateFiles" {
  source = "terraform-aws-modules/lambda/aws"

  function_name      = "sbeacon-backend-updateFiles"
  description        = "Updates the files for a project, including counting samples in VCFs"
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.12"
  memory_size        = 1769
  timeout            = 30
  attach_policy_json = true
  policy_json        = data.aws_iam_policy_document.lambda-updateFiles.json
  source_path        = "${path.module}/lambda/updateFiles"
  tags               = var.common-tags

  environment_variables = {
    DPORTAL_BUCKET        = aws_s3_bucket.dataportal-bucket.bucket
    DYNAMO_PROJECTS_TABLE = aws_dynamodb_table.projects.name
    DYNAMO_VCFS_TABLE     = aws_dynamodb_table.vcfs.name
    HTS_S3_HOST           = "s3.${var.region}.amazonaws.com"
  }

  layers = [
    local.binaries_layer,
    local.python_libraries_layer,
    local.python_modules_layer,
  ]
}

#
# dataPortal Function
#
module "lambda-data-portal" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "sbeacon-backend-dataPortal"
  description         = "Data portal endpoints."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 512
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.data-portal-lambda-access.json
  ]
  number_of_policy_jsons = 1
  source_path            = "${path.module}/lambda/dataPortal"

  tags = var.common-tags

  environment_variables = merge(
    local.sbeacon_variables,
    {
      ATHENA_METADATA_BUCKET         = aws_s3_bucket.metadata-bucket.bucket
      DYNAMO_PROJECTS_TABLE          = aws_dynamodb_table.projects.name,
      DYNAMO_PROJECT_USERS_TABLE     = aws_dynamodb_table.project_users.name,
      DYNAMO_JUPYTER_INSTANCES_TABLE = aws_dynamodb_table.juptyer_notebooks.name,
      JUPYTER_INSTACE_ROLE_ARN       = aws_iam_role.sagemaker_jupyter_instance_role.arn,
      USER_POOL_ID                   = var.cognito-user-pool-id,
      DPORTAL_BUCKET                 = aws_s3_bucket.dataportal-bucket.bucket,
      COGNITO_ADMIN_GROUP_NAME       = var.cognito-admin-group-name
      SUBMIT_LAMBDA                  = module.lambda-submitDataset.lambda_function_name
      INDEXER_LAMBDA                 = module.lambda-indexer.lambda_function_name
    },
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer,
  ]
}

#
# getProjects Function
#
module "lambda-getProjects" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "sbeacon-backend-getProjects"
  description         = "Endpoint for retrieving public project information."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 512
  timeout             = 60
  attach_policy_jsons = true
  policy_jsons = [
    data.aws_iam_policy_document.lambda-getProjects.json
  ]
  number_of_policy_jsons = 1
  source_path            = "${path.module}/lambda/getProjects"

  tags = var.common-tags

  environment_variables = merge(
    local.sbeacon_variables,
    {
      DYNAMO_PROJECTS_TABLE = aws_dynamodb_table.projects.name
    }
  )

  layers = [
    local.python_libraries_layer,
    local.python_modules_layer,
  ]
}

#
# email notification Lambda function
#
module "lambda-logEmailDelivery" {
  source = "terraform-aws-modules/lambda/aws"

  function_name       = "sbeacon-backend-logEmailDelivery"
  description         = "Logging of user invite email delivery status."
  runtime             = "python3.12"
  handler             = "lambda_function.lambda_handler"
  memory_size         = 512
  timeout             = 60
  attach_policy_jsons = true
  source_path         = "${path.module}/lambda/logEmailDelivery"

  tags = var.common-tags
}
