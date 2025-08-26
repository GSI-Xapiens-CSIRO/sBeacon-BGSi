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
set -e

echo "OnStart: Starting lifecycle configuration..."

# Setup GASPI notebooks
echo "Setting up GASPI notebooks..."
sudo unlink /home/ec2-user/sample-notebooks 2>/dev/null || true
git clone --depth 1 https://github.com/GSI-Xapiens-CSIRO/GASPI-ETL-notebooks.git /home/ec2-user/GASPI-ETL-notebooks
sudo ln -s /home/ec2-user/GASPI-ETL-notebooks /home/ec2-user/sample-notebooks

# Wait for JupyterLab to be ready
echo "Waiting for JupyterLab environment to be ready..."
sleep 120

echo "Disabling JupyterLab download extensions..."

sudo -u ec2-user -i <<'EOF'

# Wait for conda and jupyter to be available
while ! command -v jupyter >/dev/null 2>&1; do
    echo "Waiting for jupyter command..."
    sleep 10
done

# Activate JupyterSystemEnv
source activate JupyterSystemEnv

echo "Current environment: $CONDA_DEFAULT_ENV"
echo "Jupyter location: $(which jupyter)"

# Disable downloads from File > Download
echo "Disabling docmanager download extension..."
jupyter labextension disable @jupyterlab/docmanager-extension:download

# Disable downloads from the context menu in the file browser  
echo "Disabling filebrowser download extension..."
jupyter labextension disable @jupyterlab/filebrowser-extension:download

# Rebuild JupyterLab
echo "Rebuilding JupyterLab..."
jupyter lab build --minimize=False

# Verify extensions are disabled
echo "Verifying extensions are disabled:"
jupyter labextension list

# Create log file
echo "$(date): Extensions disabled successfully" > /tmp/jupyter_extensions_disabled.log

EOF

echo "OnStart lifecycle configuration completed!"

EOT
  )
}
