#!/bin/python3

import os
import yaml
import subprocess
import ast
import json

with open('properties.yml') as f:
    properties = yaml.load(f, Loader=yaml.FullLoader)

terraform_plan = properties.get('terraform_plan')

print(f'Using terraform_plan [{terraform_plan}]')
os.system(f'terraform -chdir={terraform_plan} init') 
os.system(f'terraform -chdir={terraform_plan} apply -auto-approve')


output_text = subprocess.check_output(f'terraform -chdir={terraform_plan} output -json', shell=True, text=True)
output = json.loads(output_text)
      
environment = {}
for key, value in output.items():
    environment[key] = output[key]['value']
      
with open(r'environment.yml', 'w') as environment_yml:
    documents = yaml.dump(environment, environment_yml)

