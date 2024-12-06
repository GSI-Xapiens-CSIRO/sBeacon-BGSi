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

# Keep User sagemaker Usage information
resource "aws_dynamodb_table" "sbeacon-dataportal-users-quota" {
  name           = "sbeacon-dataportal-users-quota"
  billing_mode   = "PAY_PER_REQUEST" # on demand
  #read_capacity  = 5
  #write_capacity = 5
  hash_key       = "uid"

  attribute {
    name = "uid"
    type = "S"
  }

  attribute {
    name = "CostEstimation"
    type = "S"       
  }

  attribute {
    name = "Usage"
    type = "M"
  }


  tags = {
    Owner       = "gaspi"
    Environment = "dev"
    Name        = "sbeacon-backend"
  }
}