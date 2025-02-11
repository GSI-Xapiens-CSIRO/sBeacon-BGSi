import base64
import bz2
import json
import math
import os

import boto3

EC2_IAM_INSTANCE_PROFILE = os.environ["EC2_IAM_INSTANCE_PROFILE"]
VCFS_TABLE = os.environ["DYNAMO_VCFS_TABLE"]
AWS_DEFAULT_REGION = os.environ["AWS_DEFAULT_REGION"]


REGION_AMI_MAP = {
    "ap-southeast-2": "ami-0d6560f3176dc9ec0",
    "ap-southeast-3": "ami-01ca3951ed2aa735e",
}


def launch_deidentification_ec2(
    input_bucket,
    output_bucket,
    files_table,
    project,
    file_name,
    object_key,
    size_gb,
):
    ec2_client = boto3.client("ec2")
    ami = REGION_AMI_MAP[AWS_DEFAULT_REGION]
    device_name = ec2_client.describe_images(ImageIds=[ami])["Images"][0][
        "RootDeviceName"
    ]

    with open("deidentification.py", "rb") as file:
        compressed_deidentification_script = base64.b64encode(
            bz2.compress(file.read())
        ).decode()

    ec2_startup = f"""#!/bin/bash
set -x
# Install dependencies
yum update -y
yum groupinstall -y "Development Tools"
yum install -y \
    python3 \
    python3-pip \
    awscli \
    gcc \
    make \
    zlib-devel \
    bzip2-devel \
    xz-devel \
    curl-devel \
    openssl-devel

# Install boto3 and ijson
pip install boto3
pip install ijson==3.3.0

# Configure default region
export AWS_DEFAULT_REGION={AWS_DEFAULT_REGION}

# Install bcftools and htslib
BCFTOOLS_VERSION="1.21"
HTSLIB_VERSION="1.21"
SAMTOOLS_VERSION="1.21"
curl -L https://github.com/samtools/htslib/releases/download/$HTSLIB_VERSION/htslib-$HTSLIB_VERSION.tar.bz2 | tar -xjf -
cd htslib-$HTSLIB_VERSION
./configure
make
make install
cd ..
curl -L https://github.com/samtools/bcftools/releases/download/$BCFTOOLS_VERSION/bcftools-$BCFTOOLS_VERSION.tar.bz2 | tar -xjf -
cd bcftools-$BCFTOOLS_VERSION
./configure
make
make install
cd ..
curl -L https://github.com/samtools/samtools/releases/download/$SAMTOOLS_VERSION/samtools-$SAMTOOLS_VERSION.tar.bz2 | tar -xjf -
cd samtools-$SAMTOOLS_VERSION
./configure --without-curses
make
make install
cd ..


# Verify installations
bcftools --version
htsfile --version
samtools --version

# Create project directory
mkdir -p /opt/deidentification/
cd /opt/deidentification/

# Copy contents of deidentification script
cat > ./compressed << 'EOF'
{compressed_deidentification_script}
EOF

cat > ./decompresser.py << 'EOF'
import base64
import bz2

with open("compressed", "rb") as cfile:
    with open("deidentification.py", "wb") as output:
        output.write(bz2.decompress(base64.b64decode(cfile.read())))
EOF
python3 decompresser.py

# Run deidentification
sudo -E python3 deidentification.py \
    --input-bucket '{input_bucket.replace("'", "\\'")}' \
    --output-bucket '{output_bucket.replace("'", "\\'")}' \
    --files-table '{files_table.replace("'", "\\'")}' \
    --project '{project.replace("'", "\\'")}' \
    --file-name '{file_name.replace("'", "\\'")}' \
    --object-key '{object_key.replace("'", "\\'")}'

# Check disk space
df -h
    
# Shutdown instance after processing
sudo shutdown -h now
    """

    try:
        # Launch EC2 instance
        response = ec2_client.run_instances(
            ImageId=REGION_AMI_MAP[AWS_DEFAULT_REGION],
            InstanceType="m5.large",
            MinCount=1,
            MaxCount=1,
            BlockDeviceMappings=[
                {
                    "DeviceName": device_name,
                    "Ebs": {
                        "DeleteOnTermination": True,
                        "VolumeSize": math.ceil(
                            8 + 2 * size_gb
                        ),  # Allow twice the size of the input data
                        "VolumeType": "gp3",
                        "Encrypted": True,
                    },
                },
            ],
            UserData=ec2_startup,
            InstanceInitiatedShutdownBehavior="terminate",
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [{"Key": "File", "Value": f"{object_key}"}],
                }
            ],
            IamInstanceProfile={"Name": EC2_IAM_INSTANCE_PROFILE},
        )

        instance_id = response["Instances"][0]["InstanceId"]
        print(f"Launched EC2 instance {instance_id} for deidentification")

        return {
            "statusCode": 200,
            "body": json.dumps(f"Launched EC2 instance {instance_id}"),
        }

    except Exception as e:
        print(f"Error launching EC2 instance: {str(e)}")
        return {"statusCode": 500, "body": json.dumps("Error launching EC2 instance")}
