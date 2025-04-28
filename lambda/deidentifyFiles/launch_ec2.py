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
    projects_table,
    files_table,
    project,
    file_name,
    object_key,
    size_gb,
    lambda_log_group,
    lambda_log_stream,
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

    with open("common.py", "rb") as file:
        compressed_common_script = base64.b64encode(bz2.compress(file.read())).decode()

    with open("genomic_deidentification.py", "rb") as file:
        compressed_genomic_deidentification_script = base64.b64encode(
            bz2.compress(file.read())
        ).decode()

    with open("metadata_deidentification.py", "rb") as file:
        compressed_metadata_deidentification_script = base64.b64encode(
            bz2.compress(file.read())
        ).decode()

    with open("file_validation.py", "rb") as file:
        compressed_file_validation_script = base64.b64encode(
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

pip install boto3
pip install ijson==3.3.0
pip install python-magic==0.4.27

export AWS_DEFAULT_REGION={AWS_DEFAULT_REGION}

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

# Install file
FILE_VERSION="5.46"
curl -L https://astron.com/pub/file/file-$FILE_VERSION.tar.gz | tar -xjf -
cd file-$FILE_VERSION
./configure
make
make install
cd ..

mkdir -p /opt/deidentification/logs
cd /opt/deidentification/

# Copy contents of each script
cat > ./compressed_deidentification << 'EOF'
{compressed_deidentification_script}
EOF
cat > ./compressed_common << 'EOF'
{compressed_common_script}
EOF
cat > ./compressed_genomic_deidentification << 'EOF'
{compressed_genomic_deidentification_script}
EOF
cat > ./compressed_metadata_deidentification << 'EOF'
{compressed_metadata_deidentification_script}
EOF
cat > ./compressed_file_validation << 'EOF'
{compressed_file_validation_script}
EOF

cat > ./decompresser.py << 'EOF'
import base64
import bz2

compressed_file_map = {{
    "compressed_deidentification": "deidentification.py",
    "compressed_common": "common.py", 
    "compressed_genomic_deidentification": "genomic_deidentification.py",
    "compressed_metadata_deidentification": "metadata_deidentification.py",
    "compressed_file_validation": "file_validation.py"
}}

for compressed_file, output_file in compressed_file_map.items():
    with open(compressed_file, "rb") as cfile:
        with open(output_file, "wb") as output:
            output.write(bz2.decompress(base64.b64decode(cfile.read())))
EOF
python3 decompresser.py

# Run deidentification
sudo -E python3 deidentification.py \
    --input-bucket '{input_bucket.replace("'", "\\'")}' \
    --output-bucket '{output_bucket.replace("'", "\\'")}' \
    --projects-table '{projects_table.replace("'", "\\'")}' \
    --files-table '{files_table.replace("'", "\\'")}' \
    --project '{project.replace("'", "\\'")}' \
    --file-name '{file_name.replace("'", "\\'")}' \
    --object-key '{object_key.replace("'", "\\'")}' \
    2>&1 | tee /opt/deidentification/logs/output.log
    
LOG_TIMESTAMP=$(date +%s000)

LOG_CONTENTS=$(cat /opt/deidentification/logs/output.log | jq -Rs .)

# Fallback message in case log is empty
if [[ -z "$LOG_CONTENTS" ]]; then
    LOG_CONTENTS="No output captured from deidentification.py"
fi

LOG_MESSAGE=$(echo "$LOG_CONTENTS" | jq -Rs .)

SEQUENCE_TOKEN=$(aws logs describe-log-streams \
    --log-group-name '{lambda_log_group.replace("'", "\\'")}' \
    --log-stream-name '{lambda_log_stream.replace("'", "\\'")}' \
    --query 'logStreams[0].uploadSequenceToken' --output text)

aws logs put-log-events \
    --log-group-name '{lambda_log_group.replace("'", "\\'")}' \
    --log-stream-name '{lambda_log_stream.replace("'", "\\'")}' \
    --log-events "[{{\\\"timestamp\\\":$LOG_TIMESTAMP,\\\"message\\\":$LOG_MESSAGE}}]" \
    ${{SEQUENCE_TOKEN:+--sequence-token \\"$SEQUENCE_TOKEN\\"}}

df -h
sudo shutdown -h now
    """
    print(f"User data size: {len(ec2_startup.encode('utf-8'))} bytes")

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
