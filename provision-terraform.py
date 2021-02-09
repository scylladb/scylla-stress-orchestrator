#!/bin/python3

import os
import yaml
import subprocess
import ast

with open('properties.yml') as f:
    properties = yaml.load(f, Loader=yaml.FullLoader)

terraform_plan = properties.get('terraform_plan')

print(f'Using terraform_plan {terraform_plan}')
os.system(f'terraform -chdir={terraform_plan} init') 
os.system(f'terraform -chdir={terraform_plan} apply -auto-approve')

environment = {}

def extract_output(name):
    output = subprocess.check_output(f'terraform -chdir={terraform_plan} output {name}', shell=True, text=True)
    environment[name] = ast.literal_eval(output)
    
extract_output("loadgenerator_public_ips")
extract_output("cluster_private_ips")    
extract_output("cluster_public_ips")    
        
with open(r'environment.yml', 'w') as environment_yml:
    documents = yaml.dump(environment, environment_yml)
