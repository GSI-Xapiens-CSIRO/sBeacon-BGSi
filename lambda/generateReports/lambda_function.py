import os
import base64


def lambda_handler(event, context):
    print("Backend Event Received: ", event)

    # TODO: connect to API
    data = {
        "pii_name": "John Doe",
        "pii_dob": "01-05-1990",
        "pii_gender": "Male",
    }

    # RSCM
    match event["lab"]:
        case "RSCM":
            from rscm import generate_neg, generate_pos

            if event["kind"] == "neg":
                res = generate_neg(**data)
            elif event["kind"] == "pos":
                assert len(event["variants"]) > 0, "Variants not provided"
                variants = event.get("variants", [])
                res = generate_pos(**data, variants=variants)
        case "RSSARJITO":
            from rssarjito import get_report_generator

            variants = event.get("variants", [])
            generator = get_report_generator(
                event["kind"], event["mode"], event["lang"]
            )
            if event["kind"] == "pos":
                res = generator(**data, variants=variants)
            else:
                res = generator(**data)
        case "RSPON":
            from rspon import generate

            res = generate(**data, data=data)
        case "RSJPD":
            from rsjpd import generate

            data = {
                **data,
                "apoe": event.get("apoe", None),
                "slco1b1": event.get("slco1b1", None),
            }
            res = generate(**data)
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
