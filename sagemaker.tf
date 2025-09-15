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

# Remove existing symbolic link and clone fresh notebooks repository
sudo unlink /home/ec2-user/sample-notebooks
git clone --depth 1 https://github.com/GSI-Xapiens-CSIRO/GASPI-ETL-notebooks.git /home/ec2-user/GASPI-ETL-notebooks
sudo ln -s /home/ec2-user/GASPI-ETL-notebooks /home/ec2-user/sample-notebooks

# Remove SSH clients and server packages for security
sudo yum remove -y --setopt=clean_requirements_on_remove=0 openssh-clients
sudo yum remove -y --setopt=clean_requirements_on_remove=0 openssh-server

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
  echo "Disabling JupyterLab download and export extensions..."
  jupyter labextension disable @jupyterlab/docmanager-extension:download
  jupyter labextension disable @jupyterlab/filebrowser-extension:download
  jupyter labextension disable @jupyterlab/docmanager-extension:export

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

# Remove SSH clients and server packages for security
sudo yum remove -y --setopt=clean_requirements_on_remove=0 openssh-clients
sudo yum remove -y --setopt=clean_requirements_on_remove=0 openssh-server

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
  echo "Disabling JupyterLab download and export extensions..."
  jupyter labextension disable @jupyterlab/docmanager-extension:download
  jupyter labextension disable @jupyterlab/filebrowser-extension:download
  jupyter labextension disable @jupyterlab/docmanager-extension:export

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