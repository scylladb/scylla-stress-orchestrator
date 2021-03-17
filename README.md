README

# Scylla Stress Orchestrator

The Scylla Stress Orchestrator is Python based framework for running various benchmark including cassandra-stress.

## Requirements

Scylla Stress Orchestrator requires the following tools to be installed:
- terraform
- Java 1.8+
- Awscli

## Installation

Check out the following github project

```
git clone git@github.com:pveentjer/scylla-stress-orchestrator.git
```

Set the enviroment SSO variable in e.g. your ~/.bash_profile or ~/./profile

```
export SSO=/path/to/scylla-stress-orchestrator
```

Also set the AWS access key and secret key in the same file:

```
export AWS_ACCESS_KEY_ID=<access_key>
export AWS_SECRET_ACCESS_KEY=<secret_key>

```

## Setting up a benchmark

Make a new directory containing your benchmark e.g. my-benchmark
```
mkdir my-benchmark
cd my-benchmark
```

Copy the directory ec2-generic from the scylla-stress-orchestrator. This contains an example Terraform configuration
of a complete Scylla cluster including load generator. This is where you can change the configuration of your test
environment e.g. the instance type, the number of machines etc.

Call
```
make_key
```
This will generate a public/private keypair. These keys are needed to login to the create EC2-instances.

Create a properties.yml file containing
```
---
cassandra_version: 3.11.10
load_generator_user: ubuntu
terraform_plan: ec2-generic
ssh_options: -i key -o StrictHostKeyChecking=no -o ConnectTimeout=60
jvm_path: /eng/jdk/jdk1.8.0_251/
cluster_user: ec2-user
```
Make sure the jvm_path is configured correctly.


### Provisioning

To provision the environment, call:

```
provision-terraform
```
This will provision an environment including a Scylla cluster, Scylla monitor and load generators. The result of the 
provisioning is a environment.yml file containing the ip addresses of the load generators, monitor and cluster nodes.


To destroy the environment, call the following:
```
unprovision-terraform
```

Make sure you unprovision your environment after you are done with the benchmarks, otherwise you are at risk of 
running into a very large EC2 bill.


Create a benchmark script e.g. benchmark.py:

```
#!/bin/python3

import sys
import os

sys.path.insert(1, f"{os.environ['SSO']}/src/")

from sso import common
from sso.cs import CassandraStress
from sso.common import Iteration

props = common.load_yaml('properties.yml')
env = common.load_yaml('environment.yml')
 
cluster_private_ips = env['cluster_private_ips']
cluster_string = ",".join(cluster_private_ips)

iteration = Iteration("my-benchmark")

cs = CassandraStress(env['loadgenerator_public_ips'], props)
cs.install()
cs.prepare()
cs.stress(f'write n=2m -log hdrfile=store.hdr -graph file=store.html title=store revision=benchmark-0 -mode native cql3 -rate threads=50 -node {cluster_string}')   
cs.collect_results(iteration.dir)
```

To run the benchmark, execute the following:
```
~/.benchmark.py
```

After the benchmark has run, all the results will be downloaded and can be found in 'trials/my-benchmark/'. Every time the benchmark runs, a new directory in 'trials/my-benchmark' is created with a date/time as name. 

Once the results have been downloaded, the latency distribution files are created and also the latency distribution files over all load generators so you don't need to average percentiles. Also a final summary text file is generated containing the important metrics for the benchmark like the percentiles, throughput etc.

Example:

```
WRITE-st.TotalCount=2000000
WRITE-st.Period(ms)=24174
WRITE-st.Throughput(ops/sec)=82733.52
WRITE-st.Min=112000
WRITE-st.Mean=575880.65
WRITE-st.StdDev=3727746.45
WRITE-st.50.000ptile=443135
WRITE-st.90.000ptile=950783
WRITE-st.99.000ptile=2207743
WRITE-st.99.900ptile=2994175
WRITE-st.99.990ptile=35028991
WRITE-st.99.999ptile=674234367
WRITE-st.Max=675282943
```
