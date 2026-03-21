from getpass import getpass
from vantage6.client import Client
import json


# CHANGED: Combined your config into a simple dict without Pydantic, Dynaconf, or validators
config = {
    'server_url': "https://stratafit.prod.medicaldataworks.nl",   
    'server_port': 443,
    'server_api': "/api",
    'username': "xxx",                                  
    'password': getpass("Password: "),
    'mfa_code': getpass("2FA: "),                     
    'organization_key': r"xxx"                               # Optional for encryption
}

# CHANGED: Initialize and authenticate client
client = Client(config['server_url'], config['server_port'], config['server_api'])
client.authenticate(config['username'], config['password'], mfa_code=config['mfa_code'])

if config['organization_key']:
    client.setup_encryption(config['organization_key'])    # 🔴 Optional encryption

# 🔴 OPTIONAL: List organizations and collaborations
print("Available collaborations:")
print(client.collaboration.list(fields=['id', 'name']))
print("\nAvailable organizations:")
print(client.organization.list(fields=['id', 'name']))

# 🔴 CHANGED: Define task input (you can replace this with your desired algorithm config)
task_input = {
    'method': 'validate_data',                                
    'kwargs': dict(model_name="PatientData")
}

# 🔴 CHANGED: Define task payload
task = client.task.create(
    collaboration=3,                                       
    organizations=[5],                                     
    name="demo-validation-task",
    image= "ghcr.io/strata-fit/strata-fit-data-val@sha256:c3858960054f5d2a6968c51b439fc2d9fbf7830dde1392f2875e95abe522d122", #v0.1.1
    description="validation test",
    databases=[{'label': 'dataset_202504'}],
    input_=task_input
)

# 🔴 CHANGED: Wait for results
print("\nWaiting for results...")
task_id = task["id"]
result_info = client.wait_for_results(task_id)
result_data = client.result.from_task(task_id=task_id)

# 🔴 Display nicely
print("\nResults:")
for item in result_data['data']:
    print(json.dumps(item['result'], indent=2))

