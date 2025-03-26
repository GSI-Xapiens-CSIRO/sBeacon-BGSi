import os
import base64


def lambda_handler(event, context):
    print("Backend Event Received: ", event)

    # RSCM
    match event["lab"]:
        case "RSCM":
            from rscm import generate_neg, generate_pos

            # TODO: connect to API
            data = {
                "pii_name": "John Doe",
                "pii_dob": "01-05-1990",
                "pii_gender": "Male",
            }
            if event["kind"] == "neg":
                res = generate_neg(**data)
            elif event["kind"] == "pos":
                assert len(event["variants"]) > 0, "Variants not provided"
                variants = event.get("variants", [])
                res = generate_pos(**data, variants=variants)
        case "RSPON":
            from rspon import generate

            # TODO: connect to API
            data = {
                "pii_name": "John Doe",
                "pii_dob": "01-05-1990",
                "pii_gender": "Male",
            }
            res = generate(**data, data=data)
        case _:
            return {"statusCode": 400, "body": "Invalid lab or not implemented"}

    with open(res, "rb") as f:
        binary_content = f.read()

    encoded_content = base64.b64encode(binary_content).decode("utf-8")
    os.remove(res)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/octet-stream"},
        "body": encoded_content,
    }
