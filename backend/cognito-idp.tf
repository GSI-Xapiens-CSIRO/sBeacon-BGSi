resource "aws_cognito_identity_pool" "BeaconIdentityPool" {
  identity_pool_name               = "sbeacon-users"
  allow_unauthenticated_identities = false

  cognito_identity_providers {
    client_id     = aws_cognito_user_pool_client.BeaconUserPool-client.id
    provider_name = aws_cognito_user_pool.BeaconUserPool.endpoint
  }
}

# authenticated role
data "aws_iam_policy_document" "beacon_authenticated" {
  statement {
    effect = "Allow"

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

resource "aws_iam_role" "beacon_authenticated" {
  name               = "beacon_authenticated"
  assume_role_policy = data.aws_iam_policy_document.beacon_authenticated.json
}

data "aws_iam_policy_document" "beacon_authenticated_role_policy" {
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
        "private/$${cognito-identity.amazonaws.com:sub}/saved-queries/",
        "private/$${cognito-identity.amazonaws.com:sub}/saved-queries/*",
      ]
    }
  }

  statement {
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]

    resources = [
      "${aws_s3_bucket.dataportal-bucket.arn}/private/$${cognito-identity.amazonaws.com:sub}/saved-queries/*",
    ]
  }
}

resource "aws_iam_role_policy" "beacon_authenticated" {
  name   = "authenticated_policy"
  role   = aws_iam_role.beacon_authenticated.id
  policy = data.aws_iam_policy_document.beacon_authenticated_role_policy.json
}

# unauthenticated role
data "aws_iam_policy_document" "beacon_unauthenticated" {
  statement {
    effect = "Allow"

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
      values   = ["unauthenticated"]
    }
  }
}

resource "aws_iam_role" "beacon_unauthenticated" {
  name               = "beacon_unauthenticated"
  assume_role_policy = data.aws_iam_policy_document.beacon_unauthenticated.json
}

data "aws_iam_policy_document" "beacon_unauthenticated_role_policy" {
  statement {
    effect = "Deny"

    actions = [
      "*"
    ]

    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "beacon_unauthenticated" {
  name   = "unauthenticated_policy"
  role   = aws_iam_role.beacon_unauthenticated.id
  policy = data.aws_iam_policy_document.beacon_unauthenticated_role_policy.json
}


resource "aws_cognito_identity_pool_roles_attachment" "beacon_cognito_roles" {
  identity_pool_id = aws_cognito_identity_pool.BeaconIdentityPool.id

  roles = {
    "authenticated"   = aws_iam_role.beacon_authenticated.arn
    "unauthenticated" = aws_iam_role.beacon_unauthenticated.arn
  }
}

