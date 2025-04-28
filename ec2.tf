resource "aws_iam_instance_profile" "ec2_deidentification_instance_profile" {
  name = "sbeacon_backend_ec2_deidentification_instance_profile"
  role = aws_iam_role.ec2_deidentification_instance_role.name
}

resource "aws_iam_role" "ec2_deidentification_instance_role" {
  name               = "sbeacon_backend_ec2_deidentification_instance_role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role_policy.json
}

data "aws_iam_policy_document" "ec2_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "ec2_deidentification_policy" {
  name   = "sbeacon_backend_ec2_deidentification_policy"
  role   = aws_iam_role.ec2_deidentification_instance_role.id
  policy = data.aws_iam_policy_document.ec2_deidentification_policy.json
}

data "aws_iam_policy_document" "ec2_deidentification_policy" {
  statement {
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
        "projects/*/project-files/*",
        "staging/projects/*/project-files/*",
      ]
    }
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:DeleteObject",
    ]

    resources = [
      "${aws_s3_bucket.dataportal-bucket.arn}/staging/projects/*/project-files/*",
    ]
  }

  statement {
    actions = [
      "s3:PutObject",
    ]
    resources = [
      "${aws_s3_bucket.dataportal-bucket.arn}/projects/*/project-files/*",
    ]
  }

  statement {
    actions = [
      "dynamodb:UpdateItem",
    ]
    resources = [
      aws_dynamodb_table.vcfs.arn,
      aws_dynamodb_table.projects.arn,
    ]
  }

  statement {
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams"
    ]
    resources = [
     "arn:aws:logs:${var.region}:${data.aws_caller_identity.this.account_id}:log-group:/aws/lambda/${module.lambda-deidentifyFiles.lambda_function_name}:*" 
    ]
  }
}
