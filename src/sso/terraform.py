import json
import os
import subprocess

import yaml

from os import path


def apply(terraform_plan, options=None):
    option_str = "" 
    if options:
        option_str = options
        
    print(f'Using terraform_plan [{terraform_plan}]')
    
    if not path.isdir(terraform_plan):
        print(f"Could not find directory [{terraform_plan}]")
        exit(1)

    cmd = f'terraform -chdir={terraform_plan} init'
    print(cmd)
    exitcode = subprocess.call(cmd, shell=True)
    if exitcode != 0:
        raise Exception(f'Failed terraform init, plan [{terraform_plan}], exitcode={exitcode} command=[{cmd}])')

    cmd = f'terraform -chdir={terraform_plan} apply -auto-approve {option_str}'    
    print(cmd)
    exitcode = subprocess.call(cmd, shell=True)    
    if exitcode != 0:
        raise Exception(f'Failed terraform apply, plan [{terraform_plan}], exitcode={exitcode} command=[{cmd}])')
    
    to_environment_yaml(terraform_plan)
    

def destroy(terraform_plan, options=None):
    print(f'Using terraform_plan [{terraform_plan}]')
    
    if not path.isdir(terraform_plan):
        print(f"Could not find directory [{terraform_plan}]")
        exit(1)
   
    option_str = "" 
    if options:
        option_str = options
    
    cmd = f'terraform -chdir={terraform_plan} destroy -auto-approve {option_str}'            
    print(cmd)
    exitcode = subprocess.call(cmd, shell=True)
    
    if os.path.exists("environment.yml"):
        os.remove("environment.yml")

    if exitcode != 0:
        raise Exception(f'Failed terraform destroy, plan [{terraform_plan}], exitcode={exitcode} command=[{cmd}])')
    

# Extracts all the output from a sso_terraform directory and places it into an environment.yaml
def to_environment_yaml(dir):
    output_text = subprocess.check_output(f'terraform -chdir={dir} output -json', shell=True, text=True)
    output = json.loads(output_text)

    environment = {}
    for key, value in output.items():
        environment[key] = output[key]['value']

    with open(r'environment.yml', 'w') as environment_yml:
        documents = yaml.dump(environment, environment_yml)
