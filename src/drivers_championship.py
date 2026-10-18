import os
import redis
import json

def lambda_handler(event, context):
    try:
        # Test ONLY Redis connection
        redis_host = os.environ.get("REDIS_HOST")
        r = redis.Redis(host=redis_host, port=6379, socket_timeout=3)
        r.ping()
        
        return {
            "statusCode": 200,
            "body": json.dumps({"status": "Redis connection successful!"})
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"redis_error": str(e)})
        }