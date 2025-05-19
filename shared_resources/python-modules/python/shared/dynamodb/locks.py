import boto3
import time
from botocore.exceptions import ClientError
from shared.utils import ENV_DYNAMO

dynamodb = boto3.client("dynamodb")

def acquire_lock(lock_id, owner_id, ttl_seconds):
    """
    Acquire a lock in DynamoDB with a TTL.

    :param lock_id: Unique identifier for the lock.
    :param owner_id: Unique identifier for the owner of the lock.
    :param ttl_seconds: Time-to-live in seconds for the lock.
    :return: True if the lock was acquired, False otherwise.
    """
    now = int(time.time())
    expiration_time = now + ttl_seconds

    # Step 1: Try to acquire the lock if it doesn't exist
    try:
        dynamodb.put_item(
            TableName=ENV_DYNAMO.DYNAMO_DATAPORTAL_LOCKS_TABLE,
            Item={
                "LockId": {"S": lock_id},
                "OwnerId": {"S": owner_id},
                "ExpirationTime": {"N": str(expiration_time)},
            },
            ConditionExpression="attribute_not_exists(LockId)",
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            print(f"Error acquiring lock: {e}")
            raise e

    # Step 2: Check existing lock's expiration time
    try:
        response = dynamodb.get_item(
            TableName=ENV_DYNAMO.DYNAMO_DATAPORTAL_LOCKS_TABLE, Key={"LockId": {"S": lock_id}}, ConsistentRead=True
        )

        item = response.get("Item")

        if not item:
            # Lock somehow disappeared — likely due to TTL expiration or someone else deleting it
            # This might even happen if the
            # We will just discard this attempt and let the user try again
            return False
    except ClientError as e:
        # the unlikely event of an exception
        print(f"Error retrieving lock item: {e}")
        return False

    # Step 3: Try to take over the expired lock
    current_owner = item["OwnerId"]["S"]
    current_expiration = int(item["ExpirationTime"]["N"])

    # Check if the lock is expired
    # If the lock is expired, we can try to take it over
    if current_expiration < now:
        # because we are comparing ttl outside of dynamodb
        # we need to ensure that acquiring lock is the same that we checked the ttl for
        # We need to check if the lock is still owned by the same owner
        # and if the expiration time is the same
        try:
            dynamodb.put_item(
                TableName=ENV_DYNAMO.DYNAMO_DATAPORTAL_LOCKS_TABLE,
                Item={
                    "LockId": {"S": lock_id},
                    "OwnerId": {"S": owner_id},
                    "ExpirationTime": {"N": str(expiration_time)},
                },
                ConditionExpression="OwnerId = :oldOwner AND ExpirationTime = :oldExp",
                ExpressionAttributeValues={
                    ":oldOwner": {"S": current_owner},
                    ":oldExp": {"N": str(current_expiration)},
                },
            )
            return True
        except ClientError as e:
            # Another client beat us to acquiring the expired lock
            return False

    # Lock is still valid and owned by someone else
    return False


def release_lock(lock_id, owner_id):
    """
    Release a lock in DynamoDB.
    :param lock_id: Unique identifier for the lock.
    :param owner_id: Unique identifier for the owner of the lock.
    :return: True if the lock was released, False if the lock was not owned by the requester.
    """
    try:
        dynamodb.delete_item(
            TableName=ENV_DYNAMO.DYNAMO_DATAPORTAL_LOCKS_TABLE,
            Key={"LockId": {"S": lock_id}},
            ConditionExpression="OwnerId = :ownerId",
            ExpressionAttributeValues={":ownerId": {"S": owner_id}},
        )
        # Lock released successfully
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            # Lock not owned by requester
            print(f"Lock not owned by requester: {e}")
            return False
        else:
            # Some other error occurred
            print(f"Error releasing lock: {e}")
            raise e
