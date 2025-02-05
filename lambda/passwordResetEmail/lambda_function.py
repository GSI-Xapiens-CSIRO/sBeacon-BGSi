import json

from markupsafe import escape


def lambda_handler(event, _):
    print("Event Received: {}".format(json.dumps(event)))
    if event["triggerSource"] == "CustomMessage_ForgotPassword":
        first_name = event["request"]["userAttributes"]["given_name"]
        last_name = event["request"]["userAttributes"]["family_name"]
        reset_code = event["request"]["codeParameter"]
        subject = "Data Portal Password Reset"
        body_html = f"""
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
              <h1>Hello {escape(first_name)} {escape(last_name)},</h1>
              <p>Please use the code below to reset your password.</p>
              <p>Reset Code: <strong>{reset_code}</strong></p>
              <p>Thank you,<br>Data Portal</p>
            </div>
          </body>
        </html>
        """
        event["response"]["emailSubject"] = subject
        event["response"]["emailMessage"] = body_html
        return event
