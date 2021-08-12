README

# Scylla Stress Orchestrator

The Scylla Stress Orchestrator is Python based framework for running various benchmark 
including cassandra-stress and scylla-bench.

## Requirements

Scylla Stress Orchestrator requires the following tools to be installed:
- terraform
- Java 1.8+
- Awscli

## Installation

Check out the following github project

```
git clone git@github.com:scylladb/scylla-stress-orchestrator.git
```

Set the enviroment SSO variable in e.g. your ~/.bash_profile or ~/./profile

```
export SSO=/path/to/scylla-stress-orchestrator
export PATH=$SSO/bin:$PATH
```

Also set the AWS access key and secret key in the same file:

```
export AWS_ACCESS_KEY_ID=<access_key>
export AWS_SECRET_ACCESS_KEY=<secret_key>

```

## Creating up a benchmark

Generate a benchmark using:
```
generate-benchmark foo
```
This will create a new directory `foo` with the benchmark including the EC2 configuration.
Checkout the README in the generated directory for more details.

