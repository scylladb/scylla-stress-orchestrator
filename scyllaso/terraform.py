import json
import os
import subprocess
import yaml
from os import path
from scyllaso.util import log, call, LogLevel


def apply(terraform_plan, workspace=None, options=""):
    log(f'Using terraform_plan [{terraform_plan}]')

    if not path.isdir(terraform_plan):
        log(f"Could not find directory [{terraform_plan}]", log_level=LogLevel.error)
        exit(1)

    cmd = f'terraform -chdir={terraform_plan} init'
    log(cmd)
    exitcode = call(cmd)
    if exitcode != 0:
        raise Exception(f'Failed terraform init, plan [{terraform_plan}], exitcode={exitcode} command=[{cmd}])')

    if workspace:
        cmd = f'terraform -chdir={terraform_plan} workspace select {workspace} || terraform -chdir={terraform_plan} workspace new {workspace}'
        log(cmd)
        exitcode = call(cmd, shell=True, split=False)
        if exitcode != 0:
            raise Exception(
                f'Failed terraform workspace, plan [{terraform_plan}], exitcode={exitcode} command=[{cmd}])')
        profile_file = os.path.join(os.path.abspath(os.getcwd()), workspace + ".yml")
        if path.isfile(profile_file):
            options = f'{options} -var="yaml_configuration_path={profile_file}"'

    options = f'{options} -auto-approve'

    cmd = f'terraform -chdir={terraform_plan} apply {options}'
    log(cmd)
    exitcode = call(cmd, shell=True, split=False)
    if exitcode != 0:
        raise Exception(f'Failed terraform apply, plan [{terraform_plan}], exitcode={exitcode} command=[{cmd}])')

    create_environment_yaml(terraform_plan, workspace)


def destroy(terraform_plan, workspace=None, options=""):
    log(f'Using terraform_plan [{terraform_plan}]')

    if not path.isdir(terraform_plan):
        log(f"Could not find directory [{terraform_plan}]", log_level=LogLevel.error)
        exit(1)

    if workspace:
        cmd = f'terraform -chdir={terraform_plan} workspace select {workspace}'
        log(cmd)
        exitcode = call(cmd)
        if exitcode != 0:
            raise Exception(
                f'Failed terraform workspace, plan [{terraform_plan}], exitcode={exitcode} command=[{cmd}])')
        profile_file = os.path.join(os.path.abspath(os.getcwd()), workspace + ".yml")
        if path.isfile(profile_file):
            options = f'{options} -var="yaml_configuration_path={profile_file}"'

    options = f'{options} -auto-approve'
    cmd = f'terraform -chdir={terraform_plan} destroy {options}'
    log(cmd)
    exitcode = call(cmd, shell=True, split=False)
    if exitcode != 0:
        raise Exception(f'Failed terraform destroy, plan [{terraform_plan}], exitcode={exitcode} command=[{cmd}])')

    filename = filename_environment_yml(workspace)
    if os.path.exists(filename):
        os.remove(filename)

    if workspace:
        cmd = f'terraform -chdir={terraform_plan} workspace select default && terraform -chdir={terraform_plan} workspace delete {workspace}'
        print(cmd)
        exitcode = call(cmd, shell=True, split=False)
        if exitcode != 0:
            raise Exception(
                f'Failed terraform workspace, plan [{terraform_plan}], exitcode={exitcode} command=[{cmd}])')


# Extracts all the output from a sso_terraform directory and places it into an environment.yaml
def create_environment_yaml(dir, workspace):
    output_text = subprocess.check_output(f'terraform -chdir={dir} output -json', shell=True, text=True)
    output = json.loads(output_text)

    environment = {}
    for key, value in output.items():
        environment[key] = output[key]['value']

    filename = filename_environment_yml(workspace)
    with open(filename, 'w') as environment_yml:
        yaml.dump(environment, environment_yml)


def filename_environment_yml(workspace):
    if workspace:
        return f'environment_{workspace}.yml'
    else:
        return 'environment.yml'
