resource "aws_iam_role" "sagemaker_jupyter_instance_role" {
  name               = "sbeacon_backend_sagemaker_jupyter_instance_role"
  assume_role_policy = data.aws_iam_policy_document.sagemaker_jupyter_instance_policy.json
}

data "aws_iam_policy_document" "sagemaker_jupyter_instance_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
  }
}

resource "aws_sagemaker_notebook_instance_lifecycle_configuration" "sagemaker_jupyter_instance_lcc" {
  name = "clone-gaspi-notebooks"
  on_create = base64encode(
    <<EOT
#!/bin/bash

sudo unlink /home/ec2-user/sample-notebooks
git clone --depth 1 https://github.com/GSI-Xapiens-CSIRO/GASPI-ETL-notebooks.git /home/ec2-user/GASPI-ETL-notebooks
sudo ln -s /home/ec2-user/GASPI-ETL-notebooks /home/ec2-user/sample-notebooks

EOT
  )

  on_start = base64encode(
    <<EOT
#!/bin/bash

sudo unlink /home/ec2-user/sample-notebooks
git clone --depth 1 https://github.com/GSI-Xapiens-CSIRO/GASPI-ETL-notebooks.git /home/ec2-user/GASPI-ETL-notebooks
sudo ln -s /home/ec2-user/GASPI-ETL-notebooks /home/ec2-user/sample-notebooks

EOT
  )
}
