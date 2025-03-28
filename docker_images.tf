data "aws_ecr_authorization_token" "token" {}

provider "docker" {
  registry_auth {
    address  = format("%v.dkr.ecr.%v.amazonaws.com", data.aws_caller_identity.this.account_id, var.region)
    username = data.aws_ecr_authorization_token.token.user_name
    password = data.aws_ecr_authorization_token.token.password
  }
}

#
# submitDataset docker image
data "external" "submitDataset_lambda_source_hash" {
  program     = ["python", "lambda/submitDataset/docker_prep.py"]
  working_dir = path.module
}

module "docker_image_submitDataset_lambda" {
  source = "terraform-aws-modules/lambda/aws//modules/docker-build"

  create_ecr_repo = true
  ecr_repo        = "sbeacon-submitdataset-lambda-containers"
  ecr_repo_lifecycle_policy = jsonencode({
    "rules" : [
      {
        "rulePriority" : 1,
        "description" : "Keep only the last 1 images",
        "selection" : {
          "tagStatus" : "any",
          "countType" : "imageCountMoreThan",
          "countNumber" : 1
        },
        "action" : {
          "type" : "expire"
        }
      }
    ]
    }
  )
  use_image_tag = false
  build_args = {
    SHARED_LAYER_PATH = "${path.module}/shared_resources/python-modules/python/shared"
  }
  source_path = "${path.module}/lambda/submitDataset"

  triggers = {
    dir_sha = data.external.submitDataset_lambda_source_hash.result.hash
  }

  platform = "linux/amd64"
}