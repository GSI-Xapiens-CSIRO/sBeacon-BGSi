# Generate secure random keys khusus untuk PII
resource "random_bytes" "pii_primary_key" {
  length = 32 # 256-bit AES key
}

resource "random_bytes" "pii_secondary_key" {
  length = 32 # 256-bit backup key
}

resource "random_bytes" "pii_salt" {
  length = 16 # 128-bit salt
}

resource "aws_secretsmanager_secret" "dataportal_pii_encryption" {
  name        = "sbeacon-dataportal/pii-encryption-keys"
  description = "PII encryption keys for data portal sensitive data"

  kms_key_id = aws_kms_key.pii_encryption_key.arn

  tags = merge(var.common-tags, {
    Purpose    = "PII-Encryption"
    Compliance = "HIPAA"
  })
}

resource "aws_kms_key" "pii_encryption_key" {
  description = "KMS key for PII encryption secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.this.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow Lambda access"
        Effect = "Allow"
        Principal = {
          AWS = module.lambda-data-portal.lambda_role_arn
        }
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = var.common-tags
}

resource "aws_kms_alias" "pii_encryption_key" {
  name          = "alias/sbeacon-dataportal-pii"
  target_key_id = aws_kms_key.pii_encryption_key.key_id
}

resource "aws_secretsmanager_secret_version" "dataportal_pii_encryption" {
  secret_id = aws_secretsmanager_secret.dataportal_pii_encryption.id

  secret_string = jsonencode({
    primary_key   = base64encode(random_bytes.pii_primary_key.hex)
    secondary_key = base64encode(random_bytes.pii_secondary_key.hex)
    salt          = base64encode(random_bytes.pii_salt.hex)
    version       = "v1"
    algorithm     = "AES-256-GCM"
    purpose       = "PII-DataPortal"
    created_at    = timestamp()
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}
