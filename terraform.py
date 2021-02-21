# !/bin/python3

import os
import subprocess
import yaml
import json


def apply(terraform_plan, options=None):
    print(f'Using terraform_plan [{terraform_plan}]')
    os.system(f'terraform -chdir={terraform_plan} init')
    option_str = ""
    if options:
        option_str = options
    os.system(f'terraform -chdir={terraform_plan} apply -auto-approve {option_str}')
    to_environment_yaml(terraform_plan)


def destroy(terraform_plan, options=None):
    print(f'Using terraform_plan [{terraform_plan}]')
    option_str = ""
    if options:
        option_str = options
    os.system(f'terraform -chdir={terraform_plan} destroy -auto-approve {option_str}')
    if os.path.exists("environment.yml"):
        os.remove("environment.yml")

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
