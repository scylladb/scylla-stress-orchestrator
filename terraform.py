# !/bin/python3

import os
import subprocess
import yaml
import json
import time

def apply(terraform_plan, options=None):
    option_str = "" 
    if options:
        option_str = options
        
    print(f'Using terraform_plan [{terraform_plan}]')
    
    cmd = f'terraform -chdir={terraform_plan} init'
    exitcode = os.system(cmd)
    if exitcode != 0:
        raise Exception(f'Failed terraform init, plan [{terraform_plan}], exitcode={exitcode} command=[{cmd}])')
    
    
    cmd = f'terraform -chdir={terraform_plan} apply -auto-approve {option_str}'    
    exitcode = os.system(cmd)    
    if exitcode != 0:
        raise Exception(f'Failed terraform apply, plan [{terraform_plan}], exitcode={exitcode} command=[{cmd}])')
    
    to_environment_yaml(terraform_plan)
    
    print("Giving environment time to start")
    time.sleep(5)
    print("Giving environment time to start: done")


def destroy(terraform_plan, options=None):
    print(f'Using terraform_plan [{terraform_plan}]')
    option_str = "" 
    if options:
        option_str = options
    
    cmd = f'terraform -chdir={terraform_plan} destroy -auto-approve {option_str}'            
    exitcode = os.system(cmd)
    
    if os.path.exists("environment.yml"):
        os.remove("environment.yml")

    if exitcode != 0:
        raise Exception(f'Failed terraform destroy, plan [{terraform_plan}], exitcode={exitcode} command=[{cmd}])')
    
    
    # Extracts all the output from a terraform directory and places it into


# an environment.yaml
def to_environment_yaml(dir):
    output_text = subprocess.check_output(f'terraform -chdir={dir} output -json', shell=True, text=True)
    output = json.loads(output_text)

    environment = {}
    for key, value in output.items():
        environment[key] = output[key]['value']

    with open(r'environment.yml', 'w') as environment_yml:
        documents = yaml.dump(environment, environment_yml)
