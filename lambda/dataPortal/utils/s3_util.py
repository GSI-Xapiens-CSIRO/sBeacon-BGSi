import boto3

s3 = boto3.client("s3")


def list_s3_prefix(bucket, prefix):
    continuation_token = None
    all_contents = []

    while True:
        if continuation_token:
            response = s3.list_objects_v2(
                Bucket=bucket, Prefix=prefix, ContinuationToken=continuation_token
            )
        else:
            response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

        if "Contents" in response:
            all_contents.extend(response["Contents"])

        if response.get("IsTruncated"):  # Check if there are more pages
            continuation_token = response.get("NextContinuationToken")
        else:
            break

    return [item["Key"] for item in all_contents]


def list_s3_folder(bucket, folder):
    continuation_token = None
    all_contents = []

    while True:
        if continuation_token:
            response = s3.list_objects_v2(
                Bucket=bucket,
                Prefix=folder,
                ContinuationToken=continuation_token,
                Delimiter="/",
            )
        else:
            response = s3.list_objects_v2(Bucket=bucket, Prefix=folder, Delimiter="/")

        if "CommonPrefixes" in response:
            all_contents.extend(response["CommonPrefixes"])

        if response.get("IsTruncated"):  # Check if there are more pages
            continuation_token = response.get("NextContinuationToken")
        else:
            break

    return [item["Prefix"] for item in all_contents]


def delete_s3_objects(bucket, keys):
    # S3 delete_objects API allows a maximum of 1000 keys per request
    max_keys_per_request = 1000
    responses = []

    for i in range(0, len(keys), max_keys_per_request):
        chunk = keys[i : i + max_keys_per_request]
        response = s3.delete_objects(
            Bucket=bucket, Delete={"Objects": [{"Key": key} for key in chunk]}
        )
        responses.append(response)

    return responses


def get_presigned_url(bucket, key):
    return s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=3600,
    )
