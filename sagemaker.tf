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

echo "Memulai konfigurasi lifecycle on_create..."

    # Tunggu hingga conda tersedia (maksimal 5 menit)
    echo "Menunggu conda menjadi tersedia..."
    for i in {1..300}; do
      if [ -f "/home/ec2-user/anaconda3/etc/profile.d/conda.sh" ] && source /home/ec2-user/anaconda3/etc/profile.d/conda.sh && conda info >/dev/null 2>&1; then
        echo "Conda tersedia setelah $i detik."
        break
      fi
      sleep 1
    done

    # Aktifkan environment python3 jika conda siap
    if command -v conda >/dev/null 2>&1; then
      echo "Mengaktifkan environment conda..."
      source /home/ec2-user/anaconda3/etc/profile.d/conda.sh
      conda activate python3

      # Buat handlers.py untuk melarang download
      echo "Menerapkan handlers.py untuk menonaktifkan download..."
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

      # Buat jupyter_notebook_config.py untuk mengatur handler
      echo "Menerapkan konfigurasi Jupyter..."
      cat << 'END' > /home/ec2-user/.jupyter/jupyter_notebook_config.py
import os, sys
sys.path.append('/home/ec2-user/.jupyter/')
import handlers
c.ContentsManager.files_handler_class = 'handlers.ForbidFilesHandler'
c.ContentsManager.files_handler_params = {}
END

      # Pastikan izin file benar
      echo "Mengatur izin file..."
      chown -R ec2-user:ec2-user /home/ec2-user/.jupyter
      chmod -R 755 /home/ec2-user/.jupyter

      # Restart Jupyter server untuk apply changes
      echo "Mencoba restart Jupyter server..."
      sudo systemctl restart jupyter-server || sudo /home/ec2-user/anaconda3/bin/jupyter-lab &
      echo "Konfigurasi selesai."
    else
      echo "Conda tidak tersedia setelah 5 menit, melewatkan konfigurasi."
    fi

EOT
  )

  on_start = base64encode(
    <<EOT
#!/bin/bash

sudo unlink /home/ec2-user/sample-notebooks
git clone --depth 1 https://github.com/GSI-Xapiens-CSIRO/GASPI-ETL-notebooks.git /home/ec2-user/GASPI-ETL-notebooks
sudo ln -s /home/ec2-user/GASPI-ETL-notebooks /home/ec2-user/sample-notebooks

echo "Memulai konfigurasi lifecycle on_start..."

    # Tunggu hingga conda tersedia (maksimal 5 menit)
    echo "Menunggu conda menjadi tersedia..."
    for i in {1..300}; do
      if [ -f "/home/ec2-user/anaconda3/etc/profile.d/conda.sh" ] && source /home/ec2-user/anaconda3/etc/profile.d/conda.sh && conda info >/dev/null 2>&1; then
        echo "Conda tersedia setelah $i detik."
        break
      fi
      sleep 1
    done

    # Aktifkan environment python3 jika conda siap
    if command -v conda >/dev/null 2>&1; then
      echo "Mengaktifkan environment conda..."
      source /home/ec2-user/anaconda3/etc/profile.d/conda.sh
      conda activate python3

      # Buat handlers.py untuk melarang download
      echo "Menerapkan handlers.py untuk menonaktifkan download..."
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

      # Buat jupyter_notebook_config.py untuk mengatur handler
      echo "Menerapkan konfigurasi Jupyter...menggunakan handler"
      cat << 'END' > /home/ec2-user/.jupyter/jupyter_notebook_config.py
import os, sys
sys.path.append('/home/ec2-user/.jupyter/')
import handlers
c.ContentsManager.files_handler_class = 'handlers.ForbidFilesHandler'
c.ContentsManager.files_handler_params = {}
END

      # Pastikan izin file benar
      echo "Mengatur izin file..".
      chown -R ec2-user:ec2-user /home/ec2-user/.jupyter
      chmod -R 755 /home/ec2-user/.jupyter

      # Restart Jupyter server untuk apply changes
      echo "Mencoba restart Jupyter server..."
      sudo systemctl restart jupyter-server || sudo /home/ec2-user/anaconda3/bin/jupyter-lab &
      echo "Konfigurasi selesai."
    else
      echo "Conda tidak tersedia setelah 5 menit, melewatkan konfigurasi."
    fi
EOT
  )
}