data "external" "build" {
  program = ["python", "build_and_hash.py"]
  query = {
    install_command         = var.install-command
    build_command           = var.build-command
    webapp_dir              = var.webapp-dir
    build_destiation        = var.build-destination
    base_range              = var.base_range
    region                  = var.region
    user_pool_id            = var.user_pool_id
    user_pool_web_client_id = var.user_pool_web_client_id
    api_endpoint_sbeacon    = var.api_endpoint_sbeacon
  }
  working_dir = path.module
}

resource "null_resource" "s3-upload" {
  triggers = {
    compiled_code_hash = data.external.build.result.hash
    build_file_hash    = filesha1("${path.module}/build_and_hash.py")
  }

  provisioner "local-exec" {
    command = "/bin/bash \"${path.module}/upload.sh\" \"${path.module}/${var.build-destination}\" ${aws_s3_bucket.bui-hosted-bucket.id}"
  }

  depends_on = [
    aws_s3_bucket.bui-hosted-bucket
  ]
}

resource "null_resource" "cloudfront-invalidate" {
  triggers = {
    compiled_code_hash = data.external.build.result.hash
  }

  provisioner "local-exec" {
    command = "aws cloudfront create-invalidation --distribution-id ${aws_cloudfront_distribution.bui-s3-distribution.id} --paths '/*'"
  }

  depends_on = [
    null_resource.s3-upload,
  ]
}
