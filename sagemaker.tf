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

# Disable JupyterLab download extensions via config file
echo "Creating JupyterLab config to disable download extensions..."

# Create the labconfig directory if it doesn't exist
mkdir -p /opt/conda/envs/JupyterSystemEnv/etc/jupyter/labconfig

# Check if page_config.json already exists
CONFIG_FILE="/opt/conda/envs/JupyterSystemEnv/etc/jupyter/labconfig/page_config.json"

if [ -f "$CONFIG_FILE" ]; then
    echo "Existing page_config.json found, merging with download restrictions..."
    
    # Backup existing config
    # cp "$CONFIG_FILE" "${CONFIG_FILE}.backup"
    
    # Use Python to merge JSON properly
    python3 << 'PYTHON_END'
import json
import os

config_file = "/opt/conda/envs/JupyterSystemEnv/etc/jupyter/labconfig/page_config.json"

try:
    # Read existing config
    with open(config_file, 'r') as f:
        existing_config = json.load(f)
except:
    existing_config = {}

# Add or merge disabledExtensions
if 'disabledExtensions' not in existing_config:
    existing_config['disabledExtensions'] = {}

# Add download restrictions
existing_config['disabledExtensions']['@jupyterlab/docmanager-extension:download'] = True
existing_config['disabledExtensions']['@jupyterlab/filebrowser-extension:download'] = True

# Write back the merged config
with open(config_file, 'w') as f:
    json.dump(existing_config, f, indent=2)

print("Config merged successfully")
PYTHON_END

else
    echo "No existing page_config.json, creating new one..."
    
    # Create new page_config.json
    cat > "$CONFIG_FILE" << 'CONFIG_END'
{
  "disabledExtensions": {
    "@jupyterlab/docmanager-extension:download": true,
    "@jupyterlab/filebrowser-extension:download": true
  }
}
CONFIG_END
fi

# Set proper ownership
chown -R ec2-user:ec2-user /opt/conda/envs/JupyterSystemEnv/etc/jupyter/labconfig/

echo "Final config:"
cat "$CONFIG_FILE"

echo "JupyterLab download extensions disabled via config file"
echo "$(date): Download extensions disabled via page_config.json" > /tmp/jupyter_config_applied.log

EOT
  )
}
