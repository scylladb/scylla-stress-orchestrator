#!/bin/python3

import yaml
import terraform

with open('properties.yml') as f:
    properties = yaml.load(f, Loader=yaml.FullLoader)

terraform.apply(properties.get('terraform_plan'),"-lock=false")
                
