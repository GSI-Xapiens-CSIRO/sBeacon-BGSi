#
# S3 bucket for persisted vcf summaries and variant queries
#
resource "aws_s3_bucket" "variants-bucket" {
  bucket_prefix = var.variants-bucket-prefix
  force_destroy = true
  tags          = var.common-tags
}

resource "aws_s3_bucket_ownership_controls" "variants_bucket_ownership_controls" {
  bucket = aws_s3_bucket.variants-bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "variants_bucket_acl" {
  depends_on = [aws_s3_bucket_ownership_controls.variants_bucket_ownership_controls]

  bucket = aws_s3_bucket.variants-bucket.id
  acl    = "private"
}

resource "aws_s3_bucket_lifecycle_configuration" "variants_bucket_lifecycle" {
  bucket = aws_s3_bucket.variants-bucket.id

  rule {
    id     = "clean-old-queries"
    status = "Enabled"

    filter {
      prefix = "variant-queries/"
    }

    expiration {
      days = 1
    }
  }
}

# 
# S3 bucket for metadata handling
# 
resource "aws_s3_bucket" "metadata-bucket" {
  bucket_prefix = var.metadata-bucket-prefix
  force_destroy = true
  tags          = var.common-tags
}

resource "aws_s3_bucket_ownership_controls" "metadata_bucket_ownership_controls" {
  bucket = aws_s3_bucket.metadata-bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "metadata" {
  depends_on = [aws_s3_bucket_ownership_controls.metadata_bucket_ownership_controls]

  bucket = aws_s3_bucket.metadata-bucket.id
  acl    = "private"
}

resource "aws_s3_bucket_lifecycle_configuration" "metadata_bucket_lifecycle" {
  bucket = aws_s3_bucket.metadata-bucket.id

  rule {
    id     = "clean-old-query-results"
    status = "Enabled"

    filter {
      prefix = "query-results/"
    }

    expiration {
      days = 2
    }
  }

  rule {
    id     = "clean-old-cached-results"
    status = "Enabled"

    filter {
      prefix = "query-responses/"
    }

    expiration {
      days = 2
    }
  }
}

# 
# enable cors for metadata bucket
# 
resource "aws_s3_bucket_cors_configuration" "metadata-bucket" {
  bucket = aws_s3_bucket.metadata-bucket.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = []
    max_age_seconds = 3000
  }
}

# 
# S3 bucket for lambda layers
# 
resource "aws_s3_bucket" "lambda-layers-bucket" {
  bucket_prefix = var.lambda-layers-bucket-prefix
  force_destroy = true
  tags          = var.common-tags
}

resource "aws_s3_bucket_ownership_controls" "lambda_layers_bucket_ownership_controls" {
  bucket = aws_s3_bucket.lambda-layers-bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "lambda-layers" {
  depends_on = [aws_s3_bucket_ownership_controls.lambda_layers_bucket_ownership_controls]

  bucket = aws_s3_bucket.lambda-layers-bucket.id
  acl    = "private"
}

#
# S3 bucket for data portal content
#
resource "aws_s3_bucket" "dataportal-bucket" {
  bucket_prefix = var.dataportal-bucket-prefix
  force_destroy = true
  tags          = var.common-tags
}

resource "aws_s3_bucket_versioning" "dataportal-bucket" {
  bucket = aws_s3_bucket.dataportal-bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_ownership_controls" "dataportal_bucket_ownership_controls" {
  bucket = aws_s3_bucket.dataportal-bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "dataportal_bucket_acl" {
  depends_on = [aws_s3_bucket_ownership_controls.dataportal_bucket_ownership_controls]

  bucket = aws_s3_bucket.dataportal-bucket.id
  acl    = "private"
}

resource "aws_s3_bucket_lifecycle_configuration" "staging_bucket_lifecycle" {
  bucket = aws_s3_bucket.dataportal-bucket.id

  rule {
    id     = "remove-zombie-staging-files"
    status = "Enabled"

    filter {
      prefix = "staging/"
    }

    expiration {
      days = 3
    }
  }

  rule {
    id = "expire-noncurrent-versions"
    status = "Enabled"

    filter {
      prefix = "staging/"
    }

    noncurrent_version_expiration {
      noncurrent_days = 1
    }
  }
}

# 
# enable cors for dataportal bucket
# 
resource "aws_s3_bucket_cors_configuration" "dataportal-bucket" {
  bucket = aws_s3_bucket.dataportal-bucket.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag", "x-amz-multipart-parts-count", "x-amz-abort-date"]
    max_age_seconds = 36000
  }
}

#
# Enables S3 bucket notifications for updating file information
#
resource "aws_s3_bucket_notification" "updateFiles" {
  bucket = aws_s3_bucket.dataportal-bucket.id

  lambda_function {
    lambda_function_arn = module.lambda-updateFiles.lambda_function_arn
    events = [
      "s3:ObjectCreated:*",
      "s3:ObjectRemoved:*",
    ]
    filter_prefix = "projects/"
  }

  lambda_function {
    lambda_function_arn = module.lambda-deidentifyFiles.lambda_function_arn
    events = [
      "s3:ObjectCreated:*",
    ]
    filter_prefix = "staging/projects/"
  }

  depends_on = [
    aws_lambda_permission.S3updateFiles,
    aws_lambda_permission.S3deidentifyFiles,
  ]
}
