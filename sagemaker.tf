resource "aws_iam_role" "sagemaker_jupyter_instance_role" {
  name               = "sbeacon_backend_sagemaker_jupyter_instance_role"
  assume_role_policy = data.aws_iam_policy_document.sagemaker_jupyter_instance_assume_role_policy.json
}

data "aws_iam_policy_document" "sagemaker_jupyter_instance_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "sagemaker_jupyter_instance_policy" {
  statement {
    actions   = ["s3:GetObject"]
    effect    = "Allow"
    resources = ["arn:aws:s3:::${aws_s3_bucket.dataportal-bucket.bucket}/binaries/gaspifs*"]
  }
}

resource "aws_iam_policy" "sagemaker_jupyter_instance_policy" {
  name        = "sagemaker_jupyter_instance_policy"
  description = "Policy for Sagemaker Jupyter instance to access GASPI-ETL notebooks and gaspifs binary"
  policy      = data.aws_iam_policy_document.sagemaker_jupyter_instance_policy.json
}

resource "aws_iam_role_policy_attachment" "sagemaker_jupyter_instance_role_attachment" {
  role       = aws_iam_role.sagemaker_jupyter_instance_role.name
  policy_arn = aws_iam_policy.sagemaker_jupyter_instance_policy.arn
}

resource "aws_sagemaker_notebook_instance_lifecycle_configuration" "sagemaker_jupyter_instance_lcc" {
  name = "clone-gaspi-notebooks"
  on_create = base64encode(
    <<EOT
#!/bin/bash

# Remove existing symbolic link and clone fresh notebooks repository
sudo unlink /home/ec2-user/sample-notebooks
git clone --depth 1 https://github.com/GSI-Xapiens-CSIRO/GASPI-ETL-notebooks.git /home/ec2-user/GASPI-ETL-notebooks
sudo ln -s /home/ec2-user/GASPI-ETL-notebooks /home/ec2-user/sample-notebooks

# Download gaspifs binary from S3 and set executable permissions
aws s3 cp "s3://${aws_s3_bucket.dataportal-bucket.bucket}/binaries/gaspifs" /usr/bin/gaspifs
chmod +x /usr/bin/gaspifs

# Remove SSH clients and server packages for security
sudo yum remove -y --setopt=clean_requirements_on_remove=0 openssh-clients
sudo yum remove -y --setopt=clean_requirements_on_remove=0 openssh-server

# ===== NUCLEAR OPTION: REMOVE AWS CLI COMPLETELY =====
echo "🔥 NUCLEAR: Removing AWS CLI..."

# Remove AWS CLI v2
sudo rm -rf /usr/local/aws-cli
sudo rm -f /usr/local/bin/aws
sudo rm -f /usr/local/bin/aws_completer

# Remove AWS CLI v1
sudo pip uninstall -y awscli 2>/dev/null || true
sudo pip3 uninstall -y awscli 2>/dev/null || true
sudo yum remove -y aws-cli 2>/dev/null || true

# Remove from all possible locations
sudo rm -f /usr/bin/aws
sudo rm -f /bin/aws
sudo rm -f ~/.local/bin/aws
sudo rm -rf /usr/local/aws
sudo rm /usr/local/bin/aws


# Create fake aws command that shows error
sudo tee /usr/local/bin/aws > /dev/null << 'FAKEAWS'
#!/bin/bash
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║  ❌ AWS CLI has been REMOVED from this instance               ║"
echo "║                                                                ║"
echo "║  For security reasons, AWS CLI is not available.              ║"
echo "║  If you need AWS access, please contact your administrator.   ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
exit 127
FAKEAWS

sudo chmod +x /usr/local/bin/aws

# Prevent reinstallation via pip
cat << 'PIPCONF' > /home/ec2-user/.config/pip/pip.conf
[global]
no-binary = awscli
PIPCONF

# Block in bashrc
cat << 'BASHRC' >> /home/ec2-user/.bashrc

# AWS CLI removed for security
export PATH="/usr/local/bin:$PATH"
alias aws='echo "❌ AWS CLI is disabled on this instance"'

BASHRC

echo "✓ AWS CLI completely removed"

# Remove SSH clients and server packages for security
sudo yum remove -y --setopt=clean_requirements_on_remove=0 openssh-clients
sudo yum remove -y --setopt=clean_requirements_on_remove=0 openssh-server

rm -f /home/ec2-user/anaconda3/envs/JupyterSystemEnv/bin/aws
rm -f /home/ec2-user/anaconda3/bin/aws
rm -f /usr/bin/aws

tee /home/ec2-user/anaconda3/envs/JupyterSystemEnv/bin/aws > /dev/null << 'ENDAWS'
#!/bin/bash
exit 127
ENDAWS
chmod +x /home/ec2-user/anaconda3/envs/JupyterSystemEnv/bin/aws

rm -f /home/ec2-user/anaconda3/bin/curl
rm -f /usr/bin/curl

tee /home/ec2-user/anaconda3/bin/curl > /dev/null << 'ENDCURL'
#!/bin/bash
exit 127
ENDCURL
chmod +x /home/ec2-user/anaconda3/bin/curl

rm -f /usr/bin/wget

tee /usr/local/bin/wget > /dev/null << 'ENDWGET'
#!/bin/bash
exit 127
ENDWGET
chmod +x /usr/local/bin/wget
ln -sf /usr/local/bin/wget /usr/bin/wget 2>/dev/null || true
# ========================================================

echo "Starting lifecycle on_create configuration..."

# Wait for conda to become available (maximum 5 minutes)
echo "Waiting for conda to become available..."
for i in {1..300}; do
  if [ -f "/home/ec2-user/anaconda3/etc/profile.d/conda.sh" ] && source /home/ec2-user/anaconda3/etc/profile.d/conda.sh && conda info >/dev/null 2>&1; then
    echo "Conda is available after $i seconds."
    break
  fi
  sleep 1
done

# Activate python3 environment if conda is ready
if command -v conda >/dev/null 2>&1; then
  echo "Activating conda environment..."
  source /home/ec2-user/anaconda3/etc/profile.d/conda.sh
  conda activate python3

  # Disable JupyterLab download and export extensions
  JUPYTER_BIN="/home/ec2-user/anaconda3/envs/JupyterSystemEnv/bin/jupyter"

  if [ -f "$JUPYTER_BIN" ] && $JUPYTER_BIN labextension --help >/dev/null 2>&1; then
    echo "Using JupyterSystemEnv jupyter binary"
    $JUPYTER_BIN labextension disable @jupyterlab/docmanager-extension:download
    $JUPYTER_BIN labextension disable @jupyterlab/filebrowser-extension:download  
    $JUPYTER_BIN labextension disable @jupyterlab/docmanager-extension:export
  else
    echo "JupyterSystemEnv jupyter does not support labextension, trying fallback"
  fi

  # Create handlers.py to block file downloads
  echo "Creating handlers.py to disable downloads..."
  mkdir -p /home/ec2-user/.jupyter
  cat << 'END' > /home/ec2-user/.jupyter/handlers.py
from tornado import web
from notebook.base.handlers import IPythonHandler

class ForbidFilesHandler(IPythonHandler):
  @web.authenticated
  def head(self, path):
    self.log.info("HEAD: File download forbidden.")
    raise web.HTTPError(403)

  @web.authenticated
  def get(self, path, include_body=True):
    self.log.info("GET: File download forbidden.")
    raise web.HTTPError(403)
END

  # Create jupyter_notebook_config.py to configure the handler
  echo "Applying Jupyter configuration..."
  cat << 'END' > /home/ec2-user/.jupyter/jupyter_notebook_config.py
import os, sys
sys.path.append('/home/ec2-user/.jupyter/')
import handlers
c.ContentsManager.files_handler_class = 'handlers.ForbidFilesHandler'
c.ContentsManager.files_handler_params = {}
END

  # Set correct file permissions
  echo "Setting file permissions..."
  chown -R ec2-user:ec2-user /home/ec2-user/.jupyter
  chmod -R 755 /home/ec2-user/.jupyter

  # Restart Jupyter server to apply changes
  echo "Attempting to restart Jupyter server..."
  sudo systemctl restart jupyter-server || sudo /home/ec2-user/anaconda3/bin/jupyter-lab &
  echo "Configuration completed."
else
  echo "Conda not available after 5 minutes, skipping configuration."
fi

EOT
  )

  on_start = base64encode(
    <<EOT
#!/bin/bash

# Remove existing symbolic link and clone fresh notebooks repository
sudo unlink /home/ec2-user/sample-notebooks
git clone --depth 1 https://github.com/GSI-Xapiens-CSIRO/GASPI-ETL-notebooks.git /home/ec2-user/GASPI-ETL-notebooks
sudo ln -s /home/ec2-user/GASPI-ETL-notebooks /home/ec2-user/sample-notebooks

# Download gaspifs binary from S3 and set executable permissions
aws s3 cp "s3://${aws_s3_bucket.dataportal-bucket.bucket}/binaries/gaspifs" /usr/bin/gaspifs
chmod +x /usr/bin/gaspifs

# Remove SSH clients and server packages for security
sudo yum remove -y --setopt=clean_requirements_on_remove=0 openssh-clients
sudo yum remove -y --setopt=clean_requirements_on_remove=0 openssh-server

# ===== NUCLEAR OPTION: REMOVE AWS CLI COMPLETELY =====
echo "🔥 NUCLEAR: Removing AWS CLI..."

# Remove AWS CLI v2
sudo rm -rf /usr/local/aws-cli
sudo rm -f /usr/local/bin/aws
sudo rm -f /usr/local/bin/aws_completer

# Remove AWS CLI v1
sudo pip uninstall -y awscli 2>/dev/null || true
sudo pip3 uninstall -y awscli 2>/dev/null || true
sudo yum remove -y aws-cli 2>/dev/null || true

# Remove from all possible locations
sudo rm -f /usr/bin/aws
sudo rm -f /bin/aws
sudo rm -f ~/.local/bin/aws
sudo rm -rf /usr/local/aws
sudo rm /usr/local/bin/aws


# Create fake aws command that shows error
sudo tee /usr/local/bin/aws > /dev/null << 'FAKEAWS'
#!/bin/bash
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║  ❌ AWS CLI has been REMOVED from this instance               ║"
echo "║                                                                ║"
echo "║  For security reasons, AWS CLI is not available.              ║"
echo "║  If you need AWS access, please contact your administrator.   ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
exit 127
FAKEAWS

sudo chmod +x /usr/local/bin/aws

# Prevent reinstallation via pip
cat << 'PIPCONF' > /home/ec2-user/.config/pip/pip.conf
[global]
no-binary = awscli
PIPCONF

# Block in bashrc
cat << 'BASHRC' >> /home/ec2-user/.bashrc

# AWS CLI removed for security
export PATH="/usr/local/bin:$PATH"
alias aws='echo "❌ AWS CLI is disabled on this instance"'

BASHRC

echo "✓ AWS CLI completely removed"

# Remove SSH clients and server packages for security
sudo yum remove -y --setopt=clean_requirements_on_remove=0 openssh-clients
sudo yum remove -y --setopt=clean_requirements_on_remove=0 openssh-server

rm -f /home/ec2-user/anaconda3/envs/JupyterSystemEnv/bin/aws
rm -f /home/ec2-user/anaconda3/bin/aws
rm -f /usr/bin/aws

tee /home/ec2-user/anaconda3/envs/JupyterSystemEnv/bin/aws > /dev/null << 'ENDAWS'
#!/bin/bash
exit 127
ENDAWS
chmod +x /home/ec2-user/anaconda3/envs/JupyterSystemEnv/bin/aws

rm -f /home/ec2-user/anaconda3/bin/curl
rm -f /usr/bin/curl

tee /home/ec2-user/anaconda3/bin/curl > /dev/null << 'ENDCURL'
#!/bin/bash
exit 127
ENDCURL
chmod +x /home/ec2-user/anaconda3/bin/curl

rm -f /usr/bin/wget

tee /usr/local/bin/wget > /dev/null << 'ENDWGET'
#!/bin/bash
exit 127
ENDWGET
chmod +x /usr/local/bin/wget
ln -sf /usr/local/bin/wget /usr/bin/wget 2>/dev/null || true
# ========================================================

echo "Starting lifecycle on_start configuration..."

# Wait for conda to become available (maximum 5 minutes)
echo "Waiting for conda to become available..."
for i in {1..300}; do
  if [ -f "/home/ec2-user/anaconda3/etc/profile.d/conda.sh" ] && source /home/ec2-user/anaconda3/etc/profile.d/conda.sh && conda info >/dev/null 2>&1; then
    echo "Conda is available after $i seconds."
    break
  fi
  sleep 1
done

# Activate python3 environment if conda is ready
if command -v conda >/dev/null 2>&1; then
  echo "Activating conda environment..."
  source /home/ec2-user/anaconda3/etc/profile.d/conda.sh
  conda activate python3

  # Disable JupyterLab download and export extensions
  JUPYTER_BIN="/home/ec2-user/anaconda3/envs/JupyterSystemEnv/bin/jupyter"

  if [ -f "$JUPYTER_BIN" ] && $JUPYTER_BIN labextension --help >/dev/null 2>&1; then
    echo "Using JupyterSystemEnv jupyter binary"
    $JUPYTER_BIN labextension disable @jupyterlab/docmanager-extension:download
    $JUPYTER_BIN labextension disable @jupyterlab/filebrowser-extension:download  
    $JUPYTER_BIN labextension disable @jupyterlab/docmanager-extension:export
  else
    echo "JupyterSystemEnv jupyter does not support labextension, trying fallback"
  fi

  # Create handlers.py to block file downloads
  echo "Creating handlers.py to disable downloads..."
  mkdir -p /home/ec2-user/.jupyter
  cat << 'END' > /home/ec2-user/.jupyter/handlers.py
from tornado import web
from notebook.base.handlers import IPythonHandler

class ForbidFilesHandler(IPythonHandler):
  @web.authenticated
  def head(self, path):
    self.log.info("HEAD: File download forbidden.")
    raise web.HTTPError(403)

  @web.authenticated
  def get(self, path, include_body=True):
    self.log.info("GET: File download forbidden.")
    raise web.HTTPError(403)
END

  # Create jupyter_notebook_config.py to configure the handler
  echo "Applying Jupyter configuration using custom handler..."
  cat << 'END' > /home/ec2-user/.jupyter/jupyter_notebook_config.py
import os, sys
sys.path.append('/home/ec2-user/.jupyter/')
import handlers
c.ContentsManager.files_handler_class = 'handlers.ForbidFilesHandler'
c.ContentsManager.files_handler_params = {}
END

  # Set correct file permissions
  echo "Setting file permissions..."
  chown -R ec2-user:ec2-user /home/ec2-user/.jupyter
  chmod -R 755 /home/ec2-user/.jupyter

  # Restart Jupyter server to apply changes
  echo "Attempting to restart Jupyter server..."
  sudo systemctl restart jupyter-server || sudo /home/ec2-user/anaconda3/bin/jupyter-lab &
  echo "Configuration completed."
else
  echo "Conda not available after 5 minutes, skipping configuration."
fi
EOT
  )
}
