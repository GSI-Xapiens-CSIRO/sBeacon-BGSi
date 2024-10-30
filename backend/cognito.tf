# 
# Pool and client
# 
resource "aws_cognito_user_pool" "BeaconUserPool" {
  name = "sbeacon-users"

  admin_create_user_config {
    allow_admin_create_user_only = true
    invite_message_template {
      email_subject = "sBeacon registration"
      email_message = "Welcome to sBeacon, please use username: {username} and password: {####} to log in."
      sms_message   = "Welcome to sBeacon, please use username: {username} and password: {####} to log in."
    }
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  password_policy {
    minimum_length                   = 6
    require_lowercase                = false
    require_numbers                  = false
    require_symbols                  = false
    require_uppercase                = false
    temporary_password_validity_days = 7
  }

  schema {
    name                     = "terraform"
    attribute_data_type      = "Boolean"
    developer_only_attribute = false
    mutable                  = false
    required                 = false
  }
}

resource "aws_cognito_user_pool_client" "BeaconUserPool-client" {
  name = "sbeacon-users-client"

  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id

  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_ADMIN_USER_PASSWORD_AUTH",
    "ALLOW_USER_PASSWORD_AUTH"
  ]
}

# 
# groups
# 
resource "aws_cognito_user_group" "admin-group" {
  name         = "admin-group"
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  description  = "Group of users who can has admin privileges"
  role_arn     = aws_iam_role.admin-group-role.arn
}

data "aws_iam_policy_document" "admin-group-assume-role-policy" {
  statement {
    principals {
      type        = "Federated"
      identifiers = ["cognito-identity.amazonaws.com"]
    }

    actions = ["sts:AssumeRoleWithWebIdentity"]

    condition {
      test     = "StringEquals"
      variable = "cognito-identity.amazonaws.com:aud"
      values   = [aws_cognito_identity_pool.BeaconIdentityPool.id]
    }

    condition {
      test     = "ForAnyValue:StringLike"
      variable = "cognito-identity.amazonaws.com:amr"
      values   = ["authenticated"]
    }
  }
}

resource "aws_iam_role" "admin-group-role" {
  name               = "sbeacon-admin-group-role"
  assume_role_policy = data.aws_iam_policy_document.admin-group-assume-role-policy.json
}

data "aws_iam_policy_document" "admin-group-role-policy" {
  # project access
  statement {
    actions = [
      "s3:*"
    ]
    resources = [
      "${aws_s3_bucket.dataportal-bucket.arn}/projects/*",
    ]
  }

  # private access
  statement {
    effect = "Allow"

    actions = [
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.dataportal-bucket.arn,
    ]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values = [
        "private/$${cognito-identity.amazonaws.com:sub}/",
        "private/$${cognito-identity.amazonaws.com:sub}/*",
      ]
    }
  }

  # private access
  statement {
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]

    resources = [
      "${aws_s3_bucket.dataportal-bucket.arn}/private/$${cognito-identity.amazonaws.com:sub}/*",
    ]
  }
}

resource "aws_iam_policy" "admin-group-role-policy" {
  name        = "sbeacon-admin-group-role-policy"
  description = "admin group permissions"
  policy      = data.aws_iam_policy_document.admin-group-role-policy.json

}

resource "aws_iam_role_policy_attachment" "admin-group-role-policy-attachment" {
  role       = aws_iam_role.admin-group-role.name
  policy_arn = aws_iam_policy.admin-group-role-policy.arn
}

resource "aws_cognito_user_group" "record-access" {
  name         = "record-access-user-group"
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  description  = "Group of users who can access 'record' granularity"
}

resource "aws_cognito_user_group" "count-access" {
  name         = "count-access-user-group"
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  description  = "Group of users who can access 'count' granularity"
}

resource "aws_cognito_user_group" "boolean-access" {
  name         = "boolean-access-user-group"
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  description  = "Group of users who can access 'boolean' granularity"
}

# 
# default users
# 
resource "aws_cognito_user" "guest" {
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  username     = var.beacon-guest-username
  password     = var.beacon-guest-password

  attributes = {
    terraform      = true
    email          = var.beacon-guest-username
    email_verified = true
    given_name     = "Guest"
    family_name    = "Guest"
  }
}

resource "aws_cognito_user" "admin" {
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  username     = var.beacon-admin-username
  password     = var.beacon-admin-password

  attributes = {
    terraform      = true
    given_name     = "Admin"
    family_name    = "Admin"
    email          = var.beacon-admin-username
    email_verified = true
  }
}

# 
# group assignments
# 
# admin
resource "aws_cognito_user_in_group" "admin-admin-access" {
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  group_name   = aws_cognito_user_group.admin-group.name
  username     = aws_cognito_user.admin.username
}

resource "aws_cognito_user_in_group" "admin-record-access" {
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  group_name   = aws_cognito_user_group.record-access.name
  username     = aws_cognito_user.admin.username
}

resource "aws_cognito_user_in_group" "admin-count-access" {
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  group_name   = aws_cognito_user_group.count-access.name
  username     = aws_cognito_user.admin.username
}

resource "aws_cognito_user_in_group" "admin-boolean-access" {
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  group_name   = aws_cognito_user_group.boolean-access.name
  username     = aws_cognito_user.admin.username
}

# guest
resource "aws_cognito_user_in_group" "guest-count-access" {
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  group_name   = aws_cognito_user_group.count-access.name
  username     = aws_cognito_user.guest.username
}

resource "aws_cognito_user_in_group" "guest-boolean-access" {
  user_pool_id = aws_cognito_user_pool.BeaconUserPool.id
  group_name   = aws_cognito_user_group.boolean-access.name
  username     = aws_cognito_user.guest.username
}

# 
# authorizers
# 
resource "aws_api_gateway_authorizer" "BeaconUserPool-authorizer" {
  name          = "sbeacon-userpool-authorizer"
  type          = "COGNITO_USER_POOLS"
  rest_api_id   = aws_api_gateway_rest_api.BeaconApi.id
  provider_arns = [aws_cognito_user_pool.BeaconUserPool.arn]

  depends_on = [aws_api_gateway_rest_api.BeaconApi]
}
