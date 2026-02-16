import grpc
import requests
import json
from gateway_pb2 import ActivateJobsResponse, ActivateJobsRequest, ActivatedJob, CompleteJobRequest, CompleteJobResponse
from gateway_pb2_grpc import GatewayStub
from dotenv import load_dotenv
load_dotenv()
import os

# Docling settings
from docling.document_converter import DocumentConverter

artifacts_path = "~/.cache/docling/models"
docs_path = "./docs/"

doc_converter = DocumentConverter()
# Mode settings
opp_mode = os.getenv("mode")

# Access settings Camunda
client_id = os.getenv("client_id", "")
client_secret = os.getenv("client_secret")
cluster_id = os.getenv("cluster_id", "")
region = os.getenv("region", "")
audience = os.getenv("audience")

def get_access_token(url, client_id, client_secret):
    response = requests.post(
        url,
        data={"grant_type": "client_credentials", 
              "audience": audience,
              "client_id": client_id,
              "client_secret":client_secret},
        auth=(client_id, client_secret),
    )
    return response.json()["access_token"]

def open_channel():
    if opp_mode == "self-managed":
        channel = grpc.insecure_channel("localhost:26500")
        access_token = get_access_token("http://localhost:18080/auth/realms/camunda-platform/protocol/openid-connect/token", client_id, client_secret)
        headers = [('authorization', f'Bearer {access_token}')]
    else:
        channel = grpc.secure_channel(f"{cluster_id}.{region}.zeebe.camunda.io:443", grpc.ssl_channel_credentials())
        access_token = get_access_token("https://login.cloud.camunda.io/oauth/token", client_id, client_secret)
        headers = [('authorization', f'Bearer {access_token}')]

    client = GatewayStub(channel)

    return client, access_token, headers

def activate_job(jobType):
    print(f"activating jobs of type {jobType}...")
    activate_jobs_request = ActivateJobsRequest(
        type=jobType,
        maxJobsToActivate=1,
        timeout=60000,
        requestTimeout=60000
    )
    activate_jobs_response: ActivateJobsResponse = client.ActivateJobs(activate_jobs_request, metadata=headers)
    jobsResponse = list(activate_jobs_response)
    activatedJob: ActivatedJob = jobsResponse[0].jobs[0]
    print(f"activated job: {activatedJob.key}")

    return activatedJob

def complete_job(activatedJob, variables):
    complete_job_request: CompleteJobRequest = CompleteJobRequest(
        jobKey= activatedJob.key,
        variables= json.dumps(variables)
    )
    complete_job_response: CompleteJobResponse = client.CompleteJob(complete_job_request, metadata=headers)

    return complete_job_response

def download_doc(document):
    documentId = document["documentId"]
    contentHash = document["contentHash"]
    fileMetaData = document["metadata"]
    fileName = fileMetaData["fileName"]
    if opp_mode == "self-managed":
        params = {"Authorization":f"Bearer {access_token}"}
        url = f"http://localhost:8088/v2/documents/{documentId}?contentHash={contentHash}"
        print(f"url: {url}")
    else:
        params = {"Authorization":f"Bearer {access_token}"}
        url = f"https://{region}.zeebe.camunda.io:443/{cluster_id}/v2/documents/{documentId}?contentHash={contentHash}"
    response = requests.get(url, headers=params)
    with open(f"{docs_path}{fileName}", "wb") as f:
        f.write(response.content)

    return fileName

if __name__ == "__main__":
    try:
        print("starting docling worker...")
        client, access_token, headers = open_channel()
        print("opened channel")
        while True:
            try:
                job: ActivatedJob = activate_job("converter.docling")
                variables = json.loads(job.variables)
                outputName = variables["outputVarName"]
                document = variables["document"][0]
                # download doc from Camunda
                doc_name = download_doc(document)
                # convert with docling
                result = doc_converter.convert(f'{docs_path}{doc_name}')
                markdown = result.document.export_to_markdown()
                html = result.document.export_to_html()
                variables[outputName + "_md"] = markdown
                variables[outputName + "_html"] = html
                complete_job(job, variables)
            except Exception as e:
                if e.__class__ != IndexError:
                    print(f"job worker error: {e}")
                    print(f"error class: {e.__class__}")
                    client, access_token, headers = open_channel()
                    # client, access_token, headers = open_channel()

    except Exception as e:
        print(f"Error: {e}")