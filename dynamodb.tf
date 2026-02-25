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
  # Define valid permissions per resource
  rbac_valid_permissions = {
    project_onboarding        = ["create"]
    project_management        = ["create", "read", "update", "delete"]
    notebook_management       = ["create", "read", "update", "delete"]
    file_management           = ["create", "read", "update", "delete"]
    my_project                = ["read", "download"]
    my_data                   = ["create", "read", "update", "delete", "download"]
    my_notebook               = ["create", "read", "update", "delete"]
    sbeacon_query             = ["create", "read", "update"]
    sbeacon_filter            = ["create", "read", "update"]
    clinical_workflow_execution = ["create", "read", "update"]
    igv_viewer                = ["create", "read", "update"]
    clinic_workflow_result    = ["create", "read", "update"]
    clinic_workflow_annotation = ["create", "read", "update", "delete"]
    clinic_result_validation  = ["create", "read", "update", "delete", "download"]
    clinic_request_report     = ["create", "read", "update"]
    report_validation         = ["create", "read", "update"]
    generate_report           = ["create", "read", "update"]
    faq                       = ["read", "update"]
    admin                     = ["create", "read", "update", "delete", "download"]
    profile                   = ["create", "read", "update"]
  }

  # All resources
  rbac_resources = keys(local.rbac_valid_permissions)
  
  # All standard actions
  rbac_actions = ["create", "read", "update", "delete", "download"]

  # Generate ALL permission combinations (resource x action = 100 permissions)
  # Each permission has a disabled flag: true if invalid, false if valid
  rbac_all_permissions = {
    for pair in flatten([
      for resource in local.rbac_resources : [
        for action in local.rbac_actions : {
          permission_id = "${resource}.${action}"
          resource      = resource
          action        = action
          # Check if this action is in the valid list for this resource
          disabled      = !contains(local.rbac_valid_permissions[resource], action)
        }
      ]
    ]) : pair.permission_id => pair
  }

  # Valid permissions only (for admin role assignment)
  rbac_valid_permission_ids = [
    for perm_id, perm in local.rbac_all_permissions : perm_id
    if !perm.disabled
  ]
}

# Generate UUID for admin role (created once, stored in state)
resource "random_uuid" "admin_role_id" {}

# Seed: permissions master list (all 100 combinations with disabled flag)
resource "aws_dynamodb_table_item" "seed_permissions" {
  for_each   = local.rbac_all_permissions
  table_name = aws_dynamodb_table.permissions.name
  hash_key   = aws_dynamodb_table.permissions.hash_key

  item = jsonencode({
    permission_id = { S = each.value.permission_id }
    disabled      = { BOOL = each.value.disabled }
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
    role_id     = { S = random_uuid.admin_role_id.result }
    role_name   = { S = "Administrator" }
    role_name_lower = { S = "administrator" }
    description = { S = "Full access to all resources" }
    is_active   = { BOOL = true }
  })

  lifecycle {
    ignore_changes = [item]
  }
}

# Seed: admin gets all valid (non-disabled) permissions
resource "aws_dynamodb_table_item" "seed_admin_permissions" {
  for_each   = toset(local.rbac_valid_permission_ids)
  table_name = aws_dynamodb_table.role_permissions.name
  hash_key   = aws_dynamodb_table.role_permissions.hash_key
  range_key  = aws_dynamodb_table.role_permissions.range_key

  item = jsonencode({
    role_id       = { S = random_uuid.admin_role_id.result }
    permission_id = { S = each.value }
  })

  lifecycle {
    ignore_changes = [item]
  }
}

# Seed: assign admin role to default cognito admin user
resource "aws_dynamodb_table_item" "seed_admin_user_role" {
  table_name = aws_dynamodb_table.user_roles.name
  hash_key   = aws_dynamodb_table.user_roles.hash_key
  range_key  = aws_dynamodb_table.user_roles.range_key

  item = jsonencode({
    uid     = { S = var.cognito-admin-user-sub }
    role_id = { S = random_uuid.admin_role_id.result }
  })

  lifecycle {
    ignore_changes = [item]
  }
}

#
# Guest Role Seed Data
#

# Guest role permissions - read only for specific resources
locals {
  guest_permissions = [
    "clinic_request_report",
    "clinic_workflow_annotation",
    "clinic_workflow_result",
    "clinical_workflow_execution",
    "faq",
    "file_management",
    "generate_report",
    "igv_viewer",
    "my_data",
    "my_notebook",
    "my_project",
    "profile",
  ]

  # Guest only gets read permission
  guest_permission_strings = [
    for perm in local.guest_permissions : "${perm}.read"
  ]
}

# Generate UUID for guest role
resource "random_uuid" "guest_role_id" {}

# Seed: guest role
resource "aws_dynamodb_table_item" "seed_role_guest" {
  table_name = aws_dynamodb_table.roles.name
  hash_key   = aws_dynamodb_table.roles.hash_key

  item = jsonencode({
    role_id         = { S = random_uuid.guest_role_id.result }
    role_name       = { S = "Guest" }
    role_name_lower = { S = "guest" }
    description     = { S = "Read-only access to basic resources" }
    is_active       = { BOOL = true }
  })

  lifecycle {
    ignore_changes = [item]
  }
}

# Seed: guest gets read permissions for specified resources
resource "aws_dynamodb_table_item" "seed_guest_permissions" {
  for_each   = toset(local.guest_permission_strings)
  table_name = aws_dynamodb_table.role_permissions.name
  hash_key   = aws_dynamodb_table.role_permissions.hash_key
  range_key  = aws_dynamodb_table.role_permissions.range_key

  item = jsonencode({
    role_id       = { S = random_uuid.guest_role_id.result }
    permission_id = { S = each.value }
  })

  lifecycle {
    ignore_changes = [item]
  }
}

# Seed: assign guest role to default cognito guest user
resource "aws_dynamodb_table_item" "seed_guest_user_role" {
  table_name = aws_dynamodb_table.user_roles.name
  hash_key   = aws_dynamodb_table.user_roles.hash_key
  range_key  = aws_dynamodb_table.user_roles.range_key

  item = jsonencode({
    uid     = { S = var.cognito-guest-user-sub }
    role_id = { S = random_uuid.guest_role_id.result }
  })

  lifecycle {
    ignore_changes = [item]
  }
}
