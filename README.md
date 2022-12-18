# Reverse Diagrams

> Continuous Documentation Tool - Documentation as Code Tool

This package create reverse diagrams  based on your current state in your cloud environment.

# Use

The following are the available options

```commandline
$ reverse_diagrams -h 

usage: reverse_diagrams [-h] [-c CLOUD] [-p PROFILE] [-o] [-i] [-v]

options:
  -h, --help            show this help message and exit
  -c CLOUD, --cloud CLOUD
                        Cloud Provider, aws, gcp, azure
  -p PROFILE, --profile PROFILE
                        AWS cli profile for Access Analyzer Api
  -o, --graph_organization
                        Set if you want to create graph for your organization
  -i, --graph_identity  Set if you want to create graph for your IAM Center
  -v, --version         Show version

```
For example: 

```commandline
reverse_diagrams -c aws -p my-profile -o 
```

# Cloud Providers
## AWS

### Requirement

AWS programmatic access using AWS CLI. :arrow_right: [Configuring the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)

### Service supported

#### AWS Organizations

```commandline
reverse_diagrams -c aws -p my-profile -o 
```
#### Identity and Access Manager Center (SSO)

```commandline
reverse_diagrams -c aws -p my-profile -i 
```
## Additional Commands

### Combine the options

```commandline
reverse_diagrams -c aws -p my-profile -o -i
```

