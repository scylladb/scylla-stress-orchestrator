import yaml
import argparse
from scyllaso import terraform


def get_plan(args):
    terraform_plan = args.terraform_plan
    if not terraform_plan:
        with open('properties.yml') as f:
            properties = yaml.load(f, Loader=yaml.FullLoader)
        terraform_plan = properties.get('terraform_plan')
        if not terraform_plan:
            raise Exception("Could not find 'terraform_plan' in properties.yml")
    return terraform_plan


def provision():
    parser = argparse.ArgumentParser()
    parser.add_argument("terraform_plan", help="The terraform_plan to execute (directory).", nargs='?')
    parser.add_argument("--options", nargs='?', default="")
    parser.add_argument("--workspace", nargs='?')
    args = parser.parse_args()
    terraform.apply(get_plan(args), workspace=args.workspace, options=args.options)


def unprovision():
    parser = argparse.ArgumentParser()
    parser.add_argument("terraform_plan", help="The terraform_plan to execute (directory).", nargs='?')
    parser.add_argument("--options", nargs='?', default="")
    parser.add_argument("--workspace", nargs='?')
    args = parser.parse_args()
    terraform.destroy(get_plan(args), workspace=args.workspace, options=args.options)
