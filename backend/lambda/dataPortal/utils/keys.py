import paramiko

from utils.router import PortalError

def generate_ssh_key_pair():
    key = paramiko.RSAKey.generate(2048)
    private_key_str = key.get_name() + " " + key.get_base64()
    public_key_str = f"ssh-rsa {key.get_base64()} generated-key"
    return private_key_str, public_key_str


def upload_ssh_public_key(client, instance_id, public_key, username, availability_zone):
    try:
        client.send_ssh_public_key(
            InstanceId=instance_id,
            InstanceOSUser=username,
            SSHPublicKey=public_key,
            AvailabilityZone=availability_zone
        )
        print(f"Uploaded SSH public key for user {username} on instance {instance_id}.")
    except Exception as e:
        raise PortalError(error_code=500, error_message=f"Failed to upload public key: {str(e)}")
    
"""
availability_zone = response['Instances'][0]['Placement']['AvailabilityZone']

        username = "ec2-user"

        #private_key, public_key = generate_ssh_key_pair()
        #upload_ssh_public_key(instance_id, public_key, username, availability_zone)

        #with open(f"{pipeline_name}_private_key.pem", "w") as f:
        #    f.write(private_key)
"""