resource "aws_iam_role" "ec2_nextflow_instance_role" {
  name               = "sbeacon_backend_ec2_nextflow_instance_role"
  assume_role_policy = data.aws_iam_policy_document.ec2_nextflow_instance_role.json
}

data "aws_iam_policy_document" "ec2_nextflow_instance_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}
