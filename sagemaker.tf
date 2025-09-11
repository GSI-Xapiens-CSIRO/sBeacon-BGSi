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

# Lifecycle Configuration: Disable download menu untuk JupyterLab 4
resource "aws_sagemaker_notebook_instance_lifecycle_configuration" "disable_download" {
  name = "disable-download-config"

  on_create = base64encode(<<-EOT
    #!/bin/bash
    # Pastikan direktori konfigurasi Jupyter ada
    mkdir -p /home/ec2-user/.jupyter

    # Tambahkan konfigurasi server untuk menonaktifkan download
    cat << EOF > /home/ec2-user/.jupyter/jupyter_server_config.json
    {
      "ServerApp": {
        "jpserver_extensions": {
          "jupyterlab": true
        },
        "custom_display_url": "/lab"
      },
      "LabApp": {
        "disabled_extensions": ["@jupyterlab/docmanager-extension:download", "@jupyterlab/filebrowser-extension:download"]
      }
    }
    EOF

    # Tambahkan custom JavaScript untuk override download UI
    mkdir -p /home/ec2-user/.jupyter/custom
    cat << EOF > /home/ec2-user/.jupyter/custom/custom.js
    define(['base/js/namespace'], function(Jupyter) {
      Jupyter.notebook_list.actions.remove('download-notebook');
      Jupyter.filebrowser.actions.remove('download-file');
    });
    EOF

    # Pastikan izin file benar
    chown ec2-user:ec2-user /home/ec2-user/.jupyter -R

    # Restart Jupyter server untuk apply changes
    sudo systemctl restart jupyter-server
    EOT
  )

  on_start = base64encode(<<-EOT
    #!/bin/bash
    # Pastikan konfigurasi tetap ada saat start
    mkdir -p /home/ec2-user/.jupyter
    cat << EOF > /home/ec2-user/.jupyter/jupyter_server_config.json
    {
      "ServerApp": {
        "jpserver_extensions": {
          "jupyterlab": true
        },
        "custom_display_url": "/lab"
      },
      "LabApp": {
        "disabled_extensions": ["@jupyterlab/docmanager-extension:download", "@jupyterlab/filebrowser-extension:download"]
      }
    }
    EOF

    mkdir -p /home/ec2-user/.jupyter/custom
    cat << EOF > /home/ec2-user/.jupyter/custom/custom.js
    define(['base/js/namespace'], function(Jupyter) {
      Jupyter.notebook_list.actions.remove('download-notebook');
      Jupyter.filebrowser.actions.remove('download-file');
    });
    EOF

    chown ec2-user:ec2-user /home/ec2-user/.jupyter -R
    sudo systemctl restart jupyter-server
    EOT
  )
}
