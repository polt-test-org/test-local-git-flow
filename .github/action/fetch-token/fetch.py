import json
import os
import sys
import urllib.request
import urllib.parse
import base64

sci_tenant_url = os.environ.get("SCI_TENANT_URL", "")
sci_client_id = os.environ.get("SCI_CLIENT_ID", "")

# --- Validate inputs ---
errors = []
if not sci_tenant_url:
    errors.append("SCI_TENANT_URL is required but not set")
if not sci_client_id:
    errors.append("SCI_CLIENT_ID is required but not set")
if errors:
    for e in errors:
        print(f"Error: {e}")
    sys.exit(1)

# --- Get GitLab-issued OIDC JWT ---
# GitLab injects this via id_tokens: in .gitlab-ci.yml
gitlab_jwt = os.environ.get("SCI_OIDC_TOKEN", "")
if not gitlab_jwt:
    print("Error: SCI_OIDC_TOKEN is not set — ensure id_tokens: SCI_OIDC_TOKEN is configured in the job")
    sys.exit(1)

parts = gitlab_jwt.split(".")
for part in parts[:2]:
    padded = part + "=" * (-len(part) % 4)
    print(json.dumps(json.loads(base64.b64decode(padded)), indent=2))

# --- Exchange GitLab JWT for SCI token ---
payload = urllib.parse.urlencode({
    "grant_type": "client_credentials",
    "client_id": sci_client_id,
    "resource": "urn:sap:identity:application:provider:name:build",
    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
    "client_assertion": gitlab_jwt,
}).encode()

req = urllib.request.Request(
    f"{sci_tenant_url}/oauth2/token",
    data=payload,
    method="POST",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
try:
    with urllib.request.urlopen(req) as resp:
        response = json.loads(resp.read())
except urllib.error.HTTPError as e:
    print(f"Error: SCI token request failed with status {e.code}: {e.read().decode()}")
    sys.exit(1)

sci_token = response.get("access_token")
if not sci_token:
    print(f"Error: sci_token was not retrieved. Response: {response}")
    sys.exit(1)

print("sci_token successfully retrieved")
parts = sci_token.split(".")
for part in parts[:2]:
    padded = part + "=" * (-len(part) % 4)
    print(json.dumps(json.loads(base64.b64decode(padded)), indent=2))

# Write to dotenv artifact so downstream jobs can read SCI_TOKEN
with open("token.env", "w") as f:
    f.write(f"SCI_TOKEN={sci_token}\n")
