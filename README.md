# Reverse Diagrams

> Continuous Documentation Tool - Documentation as Code Tool

This package create reverse diagrams  based on your current state in your cloud environment.

# Use

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

# Cloud Providers
## AWS

### Service supported

- AWS Organizations
- Identity and Access Manager Center (SSO)

