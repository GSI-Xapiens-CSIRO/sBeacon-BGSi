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

# Disable JupyterLab download functionality for all notebooks
echo "Setting up JupyterLab download restrictions..."

sudo -u ec2-user -i <<'EOF'

# Wait for conda environment to be ready
sleep 30

# Activate the JupyterSystemEnv environment
source activate JupyterSystemEnv

echo "Disabling JupyterLab download extensions..."

# Disable downloads from File > Download menu
jupyter labextension disable @jupyterlab/docmanager-extension:download 2>/dev/null || echo "docmanager download extension not found"

# Disable downloads from context menu in file browser
jupyter labextension disable @jupyterlab/filebrowser-extension:download 2>/dev/null || echo "filebrowser download extension not found"

# Disable save-as functionality (another way to download)
jupyter labextension disable @jupyterlab/docmanager-extension:save-as 2>/dev/null || echo "save-as extension not found"

# Optional: Disable other export functionality
# jupyter labextension disable @jupyterlab/docmanager-extension:export 2>/dev/null || echo "export extension not found"

# Rebuild JupyterLab to apply changes
echo "Rebuilding JupyterLab..."
jupyter lab build --minimize=False

echo "JupyterLab download restrictions applied successfully!"

EOF

echo "Lifecycle configuration completed"

EOT
  )
}
