# 
# sBeacon DynamoDB Tables
# 

resource "aws_dynamodb_table" "ontologies" {
  billing_mode = "PAY_PER_REQUEST"
  name         = "sbeacon-Ontologies"
  hash_key     = "id"
  tags         = var.common-tags

  attribute {
    name = "id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "descendant_terms" {
  billing_mode = "PAY_PER_REQUEST"
  name         = "sbeacon-Descendants"
  hash_key     = "term"
  tags         = var.common-tags

  attribute {
    name = "term"
    type = "S"
  }
}

resource "aws_dynamodb_table" "anscestor_terms" {
  billing_mode = "PAY_PER_REQUEST"
  name         = "sbeacon-Anscestors"
  hash_key     = "term"
  tags         = var.common-tags

  attribute {
    name = "term"
    type = "S"
  }
}

# 
# Data Portal Tables
# 

# User Projects
resource "aws_dynamodb_table" "projects" {
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "name"
  name         = "sbeacon-dataportal-projects"
  tags         = var.common-tags

  attribute {
    name = "name"
    type = "S"
  }
}

locals {
  project_users_uid_index        = "uid-index"
  clinic_jobs_project_name_index = "project-name-index"
}
# User Projects Table
resource "aws_dynamodb_table" "project_users" {
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "name"
  range_key    = "uid"
  name         = "sbeacon-dataportal-project-users"
  tags         = var.common-tags

  attribute {
    name = "name"
    type = "S"
  }

  attribute {
    name = "uid"
    type = "S"
  }

  global_secondary_index {
    name            = local.project_users_uid_index
    hash_key        = "uid"
    range_key       = "name"
    projection_type = "KEYS_ONLY"
  }
}

# Jupyter Notebooks Table
resource "aws_dynamodb_table" "juptyer_notebooks" {
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "uid"
  range_key    = "instanceName"
  name         = "sbeacon-dataportal-juptyer-notebooks"
  tags         = var.common-tags

  attribute {
    name = "uid"
    type = "S"
  }

  attribute {
    name = "instanceName"
    type = "S"
  }
}

# clinic jobs table
resource "aws_dynamodb_table" "clinic_jobs" {
  name         = "sbeacon-dataportal-clinic-jobs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "job_id"
  tags         = var.common-tags

  attribute {
    name = "job_id"
    type = "S"
  }

  attribute {
    name = "project_name"
    type = "S"
  }

  global_secondary_index {
    name            = local.clinic_jobs_project_name_index
    hash_key        = "project_name"
    projection_type = "ALL"
  }

  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"
}

# clinical annotations table
resource "aws_dynamodb_table" "clinical_annotations" {
  name         = "sbeacon-dataportal-clinical-annotations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "project_job"
  range_key    = "annotation_name"

  attribute {
    name = "project_job"
    type = "S"
  }

  attribute {
    name = "annotation_name"
    type = "S"
  }
}

# clinical variants table
resource "aws_dynamodb_table" "clinical_variants" {
  name         = "sbeacon-dataportal-clinical-variants"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "project_job"
  range_key    = "collection_name"

  attribute {
    name = "project_job"
    type = "S"
  }

  attribute {
    name = "collection_name"
    type = "S"
  }
}

# VCFs  Table
# So we can keep track of the number of samples in each vcf
resource "aws_dynamodb_table" "vcfs" {
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "vcfLocation"
  name         = "sbeacon-vcfs"
  tags         = var.common-tags

  attribute {
    name = "vcfLocation"
    type = "S"
  }
}

# Keep User sagemaker Usage information
resource "aws_dynamodb_table" "sbeacon-dataportal-users-quota" {
  name         = "sbeacon-dataportal-users-quota"
  billing_mode = "PAY_PER_REQUEST" # on demand
  #read_capacity  = 5
  #write_capacity = 5
  hash_key = "uid"

  attribute {
    name = "uid"
    type = "S"
  }

  tags = {
    Owner       = "gaspi"
    Environment = "dev"
    Name        = "sbeacon-backend"
  }
}

# saved queries trable
# this stores the saved queries of the users
resource "aws_dynamodb_table" "saved_queries" {
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "uid"
  range_key    = "name"
  name         = "sbeacon-dataportal-saved-queries"
  tags         = var.common-tags

  attribute {
    name = "uid"
    type = "S"
  }

  attribute {
    name = "name"
    type = "S"
  }
}

# dataportal locks table
resource "aws_dynamodb_table" "dataportal_locks_table" {
  name           = "sbeacon-dataportal-mutex-locks"
  billing_mode   = "PAY_PER_REQUEST" # On-demand capacity
  hash_key       = "LockId"
  tags           = var.common-tags

  attribute {
    name = "LockId"
    type = "S"
  }

  ttl {
    attribute_name = "ExpirationTime"
    enabled        = true
  }
}


# dataportal pricing cache table
resource "aws_dynamodb_table" "dataportal_pricing_cache" {
  name           = "sbeacon-dataportal-pricing-cache"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "resource"
  tags           = var.common-tags

  attribute {
    name = "resource"
    type = "S"
  }

  ttl {
    attribute_name = "ExpirationTime"
    enabled        = true
  }
}