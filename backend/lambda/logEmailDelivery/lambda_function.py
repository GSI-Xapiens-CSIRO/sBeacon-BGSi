import json


def lambda_handler(event, context):
    for record in event["Records"]:
        sns_subject = record["Sns"]["Subject"]
        if sns_subject != "Amazon SES Email Event Notification":
            continue

        sns_message = json.loads(record["Sns"]["Message"])

        event_type = sns_message.get('eventType')
        if event_type == 'Delivery':
            print(f"Email successfully delivered to: {sns_message['mail']['destination']}")
        elif event_type == 'Bounce':
            bounce_type = sns_message['bounce']['bounceType']
            bounce_sub_type = sns_message['bounce']['bounceSubType']
            print(f"Email bounced. Bounce Type: {bounce_type}, SubType: {bounce_sub_type}")
        elif event_type == 'Complaint':
            complaint_sub_type = sns_message['complaint']['complaintSubType']
            print(f"Complaint received for email: {sns_message['complaint']['complainedRecipients']}, Complaint Type: {complaint_sub_type}")
        else:
            print(f"Unknown event type: {event_type}")
        print(json.dumps(sns_message))


if __name__ == "__main__":
    pass
