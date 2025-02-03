import boto3
from markupsafe import escape

BEACON_UI_URL = ENV_BEACON.BEACON_UI_URL
SES_SOURCE_EMAIL = ENV_SES.SES_SOURCE_EMAIL
SES_CONFIG_SET_NAME = ENV_SES.SES_CONFIG_SET_NAME
cognito_client = boto3.client("cognito-idp")
ses_client = boto3.client("ses")


def lambda_handler(event, context):
    try:
        if event["triggerSource"] == "CustomMessage_ForgotPassword":
            email = event["request"]["userAttributes"]["email"]
            verification_code = event["request"]["codeParameter"]
            beacon_img_url = f"{BEACON_UI_URL}/assets/images/sbeacon.png"  # There are likely better ways of doing this, but email template is not important for now

            # Construct SES email content
            email_subject = "Your Password Reset Code"
            email_body = f"""
                <html>
                    <head>
                        <style>
                        body {{
                            font-family: Arial, sans-serif;
                            color: #333;
                        }}
                        .container {{
                            max-width: 600px;
                            margin: auto;
                            padding: 20px;
                            border: 1px solid #ddd;
                            border-radius: 5px;
                            background-color: #f9f9f9;
                        }}
                        h1 {{
                            color: #33548e;
                        }}
                        p {{
                            line-height: 1.6;
                        }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                        <h1>Hello, {escape(email)} </h1>
                        <p class="message">We received a request to reset your password. If you did not make this request, you can ignore this email. Otherwise, please input the verification code below:</p>
                        <h3>{verification_code}</h3>
                        <div style="max-width:80;">
                             <img src="{beacon_img_url}" alt="sBeacon Logo" style="max-width:80%; width:80%; margin-top:20px;">
                        </div>
                        </div>
                    </body>
                </html>
            """

            # Send email using AWS SES
            response = ses_client.send_email(
                Source=SES_SOURCE_EMAIL,
                Destination={"ToAddresses": [email]},
                Message={
                    "Subject": {"Data": email_subject, "Charset": "UTF-8"},
                    "Body": {"Html": {"Data": email_body, "Charset": "UTF-8"}},
                },
                ConfigurationSetName=SES_CONFIG_SET_NAME,
            )

            print(f"User {email} created successfully!")
            print(f"Email sent with message ID: {response["MessageId"]}")
        return event

    except Exception as e:
        print(f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    pass
