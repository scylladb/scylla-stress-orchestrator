#!/bin/python3

import os
import yaml

with open('properties.yml') as f:
    properties = yaml.load(f, Loader=yaml.FullLoader)
terraform_plan = properties.get('terraform_plan')

print(f'Using terraform_plan [{terraform_plan}]')

os.system(f'terraform -chdir={terraform_plan} destroy -auto-approve') 

if os.path.exists("environment.yml"):
    os.remove("environment.yml") 
