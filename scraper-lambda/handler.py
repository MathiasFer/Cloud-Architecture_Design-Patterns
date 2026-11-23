import json
import os
import urllib.request

def lambda_handler(event, context):
    api_url = os.getenv("API_URL", "http://localhost/reports")
    reports_to_send = [
        {"title": "Spotted Beagle", "description": "Friendly dog observed near Central Park"},
        {"title": "Injured Falcon", "description": "Falcon with injured wing on 5th Avenue"},
        {"title": "Tabby Cat", "description": "Domestic cat found wandering near library"}
    ]
    responses = []
    for r in reports_to_send:
        req = urllib.request.Request(
            api_url,
            data=json.dumps(r).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                responses.append({
                    "status_code": resp.status,
                    "body": json.loads(resp.read().decode("utf-8"))
                })
        except Exception as exc:
            responses.append({
                "status_code": 500,
                "error": str(exc)
            })
    return {
        "statusCode": 200,
        "body": json.dumps({"sent": len(reports_to_send), "results": responses})
    }
