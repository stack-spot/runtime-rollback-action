import os
import requests
import json
from pathlib import Path
from ruamel.yaml import YAML
from io import StringIO


def yaml() -> YAML:
    yml = YAML()
    yml.indent(mapping=2, sequence=4, offset=2)
    yml.allow_unicode = True
    yml.default_flow_style = False
    yml.preserve_quotes = True
    return yml


def safe_load(content: str) -> dict:
    yml = yaml()
    return yml.load(StringIO(content))


def save_output(name: str, value: str):
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output_file:
        print(f'{name}={value}', file=output_file)


def build_pipeline_url() -> str:
    GITHUB_SERVER_URL = os.getenv("GITHUB_SERVER_URL")
    GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
    GITHUB_RUN_ID = os.getenv("GITHUB_RUN_ID")
    if None in [GITHUB_SERVER_URL, GITHUB_REPOSITORY, GITHUB_RUN_ID]:
        print("- Some mandatory GitHub Action environment variable is empty.")
        exit(1)
    url = f"{GITHUB_SERVER_URL}/{GITHUB_REPOSITORY}/actions/runs/{GITHUB_RUN_ID}"
    return url

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_KEY = os.getenv("CLIENT_KEY")
CLIENT_REALM = os.getenv("CLIENT_REALM")
TF_STATE_BUCKET_NAME = os.getenv("TF_STATE_BUCKET_NAME")
TF_STATE_REGION = os.getenv("TF_STATE_REGION")
IAC_BUCKET_NAME = os.getenv("IAC_BUCKET_NAME")
IAC_REGION = os.getenv("IAC_REGION")
VERBOSE = os.getenv("VERBOSE")
VERSION_TAG = os.getenv("VERSION_TAG")
ENVIRONMENT = os.getenv("ENVIRONMENT")

inputs_list = [ENVIRONMENT, VERSION_TAG, CLIENT_ID, CLIENT_KEY, CLIENT_REALM, TF_STATE_BUCKET_NAME, TF_STATE_REGION, IAC_BUCKET_NAME, IAC_REGION]

if None in inputs_list:
    print("- Some mandatory input is empty. Please, check the input list.")
    exit(1)

with open(Path('.stk/stk.yaml'), 'r') as file:
    stk_yaml = file.read()

stk_dict = safe_load(stk_yaml)

if VERBOSE is not None:
    print("- stk.yaml:", stk_dict)

stk_yaml_type = stk_dict["spec"]["kind"]
app_or_infra_id = stk_dict["spec"]["infra-id"] if stk_yaml_type == "infra" else stk_dict["spec"]["app-id"]

print(f"{stk_yaml_type} project identified, with ID: {app_or_infra_id}")

iam_url = f"https://iam-auth-ssr.stg.stackspot.com/{CLIENT_REALM}/oidc/oauth/token"
iam_headers = {'Content-Type': 'application/x-www-form-urlencoded'}
iam_data = {"client_id": f"{CLIENT_ID}", "grant_type": "client_credentials", "client_secret": f"{CLIENT_KEY}"}

print("Authenticating...")
r1 = requests.post(
        url=iam_url, 
        headers=iam_headers, 
        data=iam_data
    )

if r1.status_code == 200:
    d1 = r1.json()
    access_token = d1["access_token"]
    
    print("Successfully authenticated!")

    request_data = {
        "appId": app_or_infra_id if stk_yaml_type != "infra" else None,
        "infraId": app_or_infra_id if stk_yaml_type == "infra" else None,
        "env": ENVIRONMENT,
        "tag": VERSION_TAG,
        "config": {
            "tfstate": {
                "bucket": TF_STATE_BUCKET_NAME,
                "region": TF_STATE_REGION
            },
            "iac": {
                "bucket": IAC_BUCKET_NAME,
                "region": IAC_REGION
            }
        },
        "pipelineUrl": build_pipeline_url()
    }

    request_data = json.dumps(request_data)

    if VERBOSE is not None:
        print("- ROLLBACK RUN REQUEST DATA:", request_data)
    
    deploy_headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    print("Deploying Self-Hosted Rollback..")

    if stk_yaml_type == 'app':
        self_hosted_rollback_app_url = "https://runtime-manager.stg.stackspot.com/v1/run/self-hosted/rollback/app"
        rollback_request = requests.post(
                url=self_hosted_rollback_app_url,
                headers=deploy_headers,
                data=request_data
            )
    elif stk_yaml_type == 'infra':
        self_hosted_rollback_infra_url = "https://runtime-manager.stg.stackspot.com/v1/run/self-hosted/rollback/infra"
        rollback_request = requests.post(
                url=self_hosted_rollback_infra_url,
                headers=deploy_headers,
                data=request_data
            )
    else:
        print("- STK TYPE not recognized. Please, check the input.")
        exit(1)

    if rollback_request.status_code == 201:
        d2 = rollback_request.json()
        runId = d2["runId"]
        runType = d2["runType"]
        tasks = d2["tasks"]

        save_output('tasks', tasks)
        save_output('run_id', runId)

        print(f"- Rollback RUN {runType} successfully started with ID: {runId}")
        print(f"- Rollback RUN TASKS LIST: {tasks}")

    else:
        print("- Error starting self hosted rollback run")
        print("- Status:", rollback_request.status_code)
        print("- Error:", rollback_request.reason)
        print("- Response:", rollback_request.text)
        exit(1)

else:
    print("- Error during IAM authentication")
    print("- Status:", r1.status_code)
    print("- Error:", r1.reason)
    print("- Response:", r1.text)
    exit(1)
