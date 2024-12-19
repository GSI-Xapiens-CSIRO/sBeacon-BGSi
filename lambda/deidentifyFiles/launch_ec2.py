import boto3
import json
import os

EC2_IAM_INSTANCE_PROFILE = os.environ["EC2_IAM_INSTANCE_PROFILE"]
VCFS_TABLE = os.environ["DYNAMO_VCFS_TABLE"]
AWS_DEFAULT_REGION = os.environ["AWS_DEFAULT_REGION"]

def launch_deidentification_ec2(
        input_bucket,
        output_bucket,
        files_table,
        project,
        file_name,
        object_key,
    ):
    ec2_client = boto3.client('ec2')
    
    with open('deidentification.py', 'r') as file:
        deidentification_script = file.read()

    ec2_startup = f'''#!/bin/bash

exec > /var/log/deidentification-setup.log 2>&1

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

# Install boto3
pip install boto3

# Configure default region
export AWS_DEFAULT_REGION={AWS_DEFAULT_REGION}

# Install bcftools and htslib
BCFTOOLS_VERSION="1.17"
HTSLIB_VERSION="1.17"
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

# Verify installations
bcftools --version
htsfile --version

# Create project directory
mkdir -p /opt/deidentification/
cd /opt/deidentification/

# Copy contents of deidentification script
cat > ./deidentification.py << 'EOF'
{deidentification_script}
EOF

# Run deidentification
sudo -E python3 deidentification.py \
    --input-bucket {input_bucket} \
    --output-bucket {output_bucket} \
    --files-table {files_table} \
    --project {project} \
    --file-name {file_name} \
    --object-key {object_key}

# Shutdown instance after processing
sudo shutdown -h now
    '''
    
    try:
        # Launch EC2 instance
        response = ec2_client.run_instances(
            ImageId='ami-0d6560f3176dc9ec0',
            KeyName='edw222',
            InstanceType='t2.micro',
            MinCount=1,
            MaxCount=1,
            UserData=ec2_startup,
            #InstanceInitiatedShutdownBehavior='terminate',
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'File',
                            'Value': f'{object_key}'
                        }
                    ]
                }
            ],
            IamInstanceProfile={"Name": EC2_IAM_INSTANCE_PROFILE}
        )
        
        instance_id = response['Instances'][0]['InstanceId']
        print(f"Launched EC2 instance {instance_id} for deidentification")
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Launched EC2 instance {instance_id}')
        }
    
    except Exception as e:
        print(f"Error launching EC2 instance: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error launching EC2 instance')
        }