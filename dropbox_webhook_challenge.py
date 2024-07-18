import json


def lambda_handler(event, context):
    query_params = event.get("queryStringParameters", {})
    challenge = query_params.get("challenge")
    if isinstance(challenge, bytes):
        challenge = challenge.decode("utf-8")
    # Otherwise, ensure it's a string
    else:
        challenge = str(challenge)
    return {
        "statusCode": 200,
        "body": challenge,
        "headers": {"Content-Type": "text/plain", "X-Content-Type-Options": "nosniff"},
    }
