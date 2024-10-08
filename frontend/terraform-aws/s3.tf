# bucket definition
resource "aws_s3_bucket" "bui-hosted-bucket" {
  bucket_prefix = "bui-bucket-${terraform.workspace}-"
  force_destroy = true
  tags          = var.common-tags
}

# allow cloudfront to access s3
resource "aws_s3_bucket_policy" "s3_access_from_cloudfront" {
  bucket = aws_s3_bucket.bui-hosted-bucket.id
  policy = data.aws_iam_policy_document.s3_access_from_cloudfront.json
}

# iam policy
data "aws_iam_policy_document" "s3_access_from_cloudfront" {
  statement {
    principals {
      type = "Service"
      identifiers = [
        "cloudfront.amazonaws.com"
      ]
    }

    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${aws_s3_bucket.bui-hosted-bucket.arn}/*"
    ]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values = [
        aws_cloudfront_distribution.bui-s3-distribution.arn
      ]
    }
  }
}
