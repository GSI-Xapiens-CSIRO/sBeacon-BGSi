locals {
  project_users_uid_index        = "uid-index"
  clinic_jobs_project_name_index = "project-name-index"
  cli_uploads_project_name_index = "cli-uploads-project-name-index"
  user_roles_role_id_index       = "role-id-index"
  role_permissions_perm_id_index = "permission-id-index"
}

# 
# sBeacon DynamoDB Tables
# 

resource "aws_dynamodb_table" "ontologies" {
  billing_mode = "PAY_PER_REQUEST"
  name         = "sbeacon-Ontologies"
  hash_key     = "id"

  tags = merge(var.common-tags, var.common-tags-backup)

  attribute {
    name = "id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "descendant_terms" {
  billing_mode = "PAY_PER_REQUEST"
  name         = "sbeacon-Descendants"
  hash_key     = "term"

  tags = merge(var.common-tags, var.common-tags-backup)

  attribute {
    name = "term"
    type = "S"
  }
}

resource "aws_dynamodb_table" "anscestor_terms" {
  billing_mode = "PAY_PER_REQUEST"
  name         = "sbeacon-Anscestors"
  hash_key     = "term"

  tags = merge(var.common-tags, var.common-tags-backup)

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

  tags = merge(var.common-tags, var.common-tags-backup)

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

  tags = merge(var.common-tags, var.common-tags-backup)

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

  tags = merge(var.common-tags, var.common-tags-backup)

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

  tags = merge(var.common-tags, var.common-tags-backup)

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

  tags = merge(var.common-tags, var.common-tags-backup)

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

  tags = merge(var.common-tags, var.common-tags-backup)

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

  tags = merge(var.common-tags, var.common-tags-backup)

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

  tags = merge({
    Owner       = "gaspi"
    Environment = "dev"
    Name        = "sbeacon-backend"
    },
    var.common-tags-backup
  )
}

resource "aws_dynamodb_table" "sbeacon_dataportal_users_info" {
  name         = "sbeacon-dataportal-users-info"
  billing_mode = "PAY_PER_REQUEST" # on demand
  #read_capacity  = 5
  #write_capacity = 5
  hash_key = "uid"

  attribute {
    name = "uid"
    type = "S"
  }

  tags = merge(var.common-tags, var.common-tags-backup)
}

# saved queries trable
# this stores the saved queries of the users
resource "aws_dynamodb_table" "saved_queries" {
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "uid"
  range_key    = "name"
  name         = "sbeacon-dataportal-saved-queries"

  tags = merge(var.common-tags, var.common-tags-backup)

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
  name         = "sbeacon-dataportal-mutex-locks"
  billing_mode = "PAY_PER_REQUEST" # On-demand capacity
  hash_key     = "LockId"

  tags = merge(var.common-tags, var.common-tags-backup)

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
  name         = "sbeacon-dataportal-pricing-cache"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "resource"

  tags = merge(var.common-tags, var.common-tags-backup)

  attribute {
    name = "resource"
    type = "S"
  }

  ttl {
    attribute_name = "ExpirationTime"
    enabled        = true
  }
}

# dataportal cli upload table
resource "aws_dynamodb_table" "dataportal_cli_upload" {
  name         = "sbeacon-dataportal-cli-upload"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "uid"
  range_key    = "upload_id"

  tags = merge(var.common-tags, var.common-tags-backup)

  attribute {
    name = "uid"
    type = "S"
  }

  attribute {
    name = "upload_id"
    type = "S"
  }

  attribute {
    name = "project_name"
    type = "S"
  }

  ttl {
    attribute_name = "ExpirationTime"
    enabled        = true
  }

  global_secondary_index {
    name            = local.cli_uploads_project_name_index
    hash_key        = "project_name"
    range_key       = "uid"
    projection_type = "ALL"
  }
}

#
# RBAC Tables
#

# Roles table
resource "aws_dynamodb_table" "roles" {
  name         = "sbeacon-dataportal-roles"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "role_id"

  tags = merge(var.common-tags, var.common-tags-backup)

  attribute {
    name = "role_id"
    type = "S"
  }
}

# Permissions table
resource "aws_dynamodb_table" "permissions" {
  name         = "sbeacon-dataportal-permissions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "permission_id"

  tags = merge(var.common-tags, var.common-tags-backup)

  attribute {
    name = "permission_id"
    type = "S"
  }
}

# Role Permissions table
# Maps role to permission strings (e.g. "project_onboarding.create", "project_onboarding.read")
# If the row exists, the role has that permission
resource "aws_dynamodb_table" "role_permissions" {
  name         = "sbeacon-dataportal-role-permissions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "role_id"
  range_key    = "permission_id"

  tags = merge(var.common-tags, var.common-tags-backup)

  attribute {
    name = "role_id"
    type = "S"
  }

  attribute {
    name = "permission_id"
    type = "S"
  }

  global_secondary_index {
    name            = local.role_permissions_perm_id_index
    hash_key        = "permission_id"
    range_key       = "role_id"
    projection_type = "ALL"
  }
}

# User Roles table
resource "aws_dynamodb_table" "user_roles" {
  name         = "sbeacon-dataportal-user-roles"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "uid"
  range_key    = "role_id"

  tags = merge(var.common-tags, var.common-tags-backup)

  attribute {
    name = "uid"
    type = "S"
  }

  attribute {
    name = "role_id"
    type = "S"
  }

  global_secondary_index {
    name            = local.user_roles_role_id_index
    hash_key        = "role_id"
    range_key       = "uid"
    projection_type = "ALL"
  }
}

#
# RBAC Seed Data
#

locals {
  rbac_permissions = [
    "project_onboarding",
    "project_management",
    "notebook_management",
    "file_management",
    "my_project",
    "my_data",
    "my_notebook",
    "sbeacon_query",
    "sbeacon_filter",
    "clinical_workflow_execution",
    "igv_viewer",
    "clinic_workflow_result",
    "clinic_workflow_annotation",
    "clinic_result_validation",
    "clinic_request_report",
    "report_validation",
    "generate_report",
    "faq",
    "admin",
    "profile",
  ]

  rbac_access_types = ["create", "read", "update", "delete", "download"]

  # Generate all permission strings: resource.action
  rbac_permission_strings = flatten([
    for perm in local.rbac_permissions : [
      for access in local.rbac_access_types : "${perm}.${access}"
    ]
  ])
}

# Seed: permissions master list
resource "aws_dynamodb_table_item" "seed_permissions" {
  for_each   = toset(local.rbac_permission_strings)
  table_name = aws_dynamodb_table.permissions.name
  hash_key   = aws_dynamodb_table.permissions.hash_key

  item = jsonencode({
    permission_id = { S = each.value }
  })

  lifecycle {
    ignore_changes = [item]
  }
}

# Seed: admin role
resource "aws_dynamodb_table_item" "seed_role_admin" {
  table_name = aws_dynamodb_table.roles.name
  hash_key   = aws_dynamodb_table.roles.hash_key

  item = jsonencode({
    role_id     = { S = "admin" }
    role_name   = { S = "Administrator" }
    description = { S = "Full access to all resources" }
  })

  lifecycle {
    ignore_changes = [item]
  }
}

# Seed: admin gets all permissions
resource "aws_dynamodb_table_item" "seed_admin_permissions" {
  for_each   = toset(local.rbac_permission_strings)
  table_name = aws_dynamodb_table.role_permissions.name
  hash_key   = aws_dynamodb_table.role_permissions.hash_key
  range_key  = aws_dynamodb_table.role_permissions.range_key

  item = jsonencode({
    role_id       = { S = "admin" }
    permission_id = { S = each.value }
  })

  lifecycle {
    ignore_changes = [item]
  }
}
