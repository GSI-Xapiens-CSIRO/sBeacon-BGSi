import json
import os
import re
from datetime import datetime


def lambda_handler(event, context):
    """
    Public endpoint to log authentication activities from Amplify/Cognito
    No JWT required - designed for pre-auth and post-auth events
    
    Accepts any JSON payload with minimal validation:
    - Must have 'email' field (for indexing/filtering)
    - Everything else is dynamic and logged as-is
    
    Example payloads:
    {
        "email": "user@example.com",
        "event_type": "login",
        "status": "success",
        "metadata": {...}
    }
    
    {
        "email": "user@example.com",
        "event": "mfa_verify",
        "result": "failed",
        "reason": "invalid_code",
        "custom_field": "any_value"
    }
    """
    try:
        # Parse request body
        if isinstance(event.get('body'), str):
            body = json.loads(event.get('body', '{}'))
        else:
            body = event.get('body', {})
        
        # Minimal validation - only require email
        email = body.get('email')
        
        # Email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not email or not re.match(email_pattern, email):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'success': False,
                    'message': 'Invalid or missing email field'
                })
            }
        
        # Get client IP and user agent for security logging
        source_ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')
        user_agent = event.get('headers', {}).get('User-Agent', 'unknown')
        
        # Create log entry with ALL payload data
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'source_ip': source_ip,
            'user_agent': user_agent,
            **body  # Spread all payload fields into log entry
        }
        
        # Log to CloudWatch (structured JSON)
        print(json.dumps(log_entry))
        
        # TODO: Store to DynamoDB if needed
        # Can be added later when DynamoDB table is created
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',  # For CORS
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'message': 'Activity logged successfully',
                'timestamp': timestamp
            })
        }
        
    except json.JSONDecodeError as e:
        print(f"Invalid JSON payload: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': False,
                'message': 'Invalid JSON payload'
            })
        }
    except Exception as e:
        print(f"Error logging auth activity: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': False,
                'message': 'Internal server error'
            })
        }

