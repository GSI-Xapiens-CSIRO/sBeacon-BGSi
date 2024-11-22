resource "aws_dynamodb_table" "datasets" {
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  name         = "sbeacon-Datasets"
  tags         = var.common-tags

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "assemblyId"
    type = "S"
  }

  global_secondary_index {
    hash_key = "assemblyId"
    name     = "assembly_index"
    non_key_attributes = [
      "id",
      "vcfLocations",
      "vcfGroups",
      "vcfChromosomeMap"
    ]
    projection_type = "INCLUDE"
  }
}

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

# this table holds the query made by user
# this is used to control the lambdas that
# execute a given query
# resonses counts the completed lambdas
resource "aws_dynamodb_table" "variant_queries" {
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  name         = "sbeacon-VariantQueries"
  tags         = var.common-tags

  attribute {
    name = "id"
    type = "S"
  }

  # enable this later to save cost
  ttl {
    attribute_name = "timeToExist"
    enabled        = true
  }
}

# this table holds responses by perform query operation
# responseIndex is used to order and paginate
# this points to a JSON files with results
resource "aws_dynamodb_table" "variant_query_responses" {
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  range_key    = "responseNumber"
  name         = "sbeacon-VariantQueryResponses"
  tags         = var.common-tags

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "responseNumber"
    type = "N"
  }

  local_secondary_index {
    range_key       = "responseNumber"
    name            = "responseNumber_index"
    projection_type = "ALL"
  }

  # enable this later to save cost
  ttl {
    attribute_name = "timeToExist"
    enabled        = true
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
