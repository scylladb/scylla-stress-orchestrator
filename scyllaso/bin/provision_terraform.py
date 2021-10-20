import yaml
import os
import argparse
from scyllaso import terraform


def get_plan(args):
    terraform_plan = args.terraform_plan
    if terraform_plan:
        return terraform_plan

    if not os.path.exists("properties.yml"):
        print("No terraform_plan has been configured and 'properties.yml' does not exist.")
        exit(1)

    with open('properties.yml') as f:
        properties = yaml.load(f, Loader=yaml.FullLoader)

    terraform_plan = properties.get('terraform_plan')
    if not terraform_plan:
        print("No terraform_plan has been configured and terraform_plan was not found in properties.yml.")
        exit(1)
    return terraform_plan


def provision():
    parser = argparse.ArgumentParser()
    parser.add_argument("terraform_plan", help="The terraform_plan to execute (directory).", nargs='?')
    parser.add_argument("--options", help="Additional Terraform options", default="")
    parser.add_argument("--workspace", help="Specifies the Terraform workspace")
    args = parser.parse_args()
    terraform.apply(get_plan(args), workspace=args.workspace, options=args.options)


def unprovision():
    parser = argparse.ArgumentParser()
    parser.add_argument("terraform_plan", help="The terraform_plan to execute (directory).", nargs='?')
    parser.add_argument("--options", help="Additional Terraform options", default="")
    parser.add_argument("--workspace", help="Specifies the Terraform workspace")
    args = parser.parse_args()
    terraform.destroy(get_plan(args), workspace=args.workspace, options=args.options)
