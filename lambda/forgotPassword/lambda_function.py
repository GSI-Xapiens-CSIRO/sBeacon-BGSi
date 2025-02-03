def lambda_handler(event, context):
    if event["triggerSource"] == "CustomMessage_ForgotPassword":
        event["response"]["emailSubject"] = "Your Password Reset Code"
        event["response"][
            "emailMessage"
        ] = f"""
        Hello {event['request']['userAttributes']['email']},

        Your password reset code is: {event['request']['codeParameter']}

        This code will expire in 24 hours.
        Testing.
        """

    return event


if __name__ == "__main__":
    pass
