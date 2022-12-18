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
Date: 2022-12-17 22:33:21.791819
🔄 Getting Organization Info
🔄 The Organizational Units list 
🔄 Getting the Account list info
Run -> python3 graph_org.py 

```
Then run `python3 graph_org.py` to create a png screenshot (`organizations-state.png`) for your current state.

> Both files are saved into the current directory.

```commandline
$  reverse_diagrams -c aws -p labvel-master -o
Date: 2022-12-17 22:44:07.623260
🔄 Getting Organization Info
🔄 The Organizational Units list 
🔄 Getting the Account list info
Run -> python3 graph_org.py 


$ python3 graph_org.py 
$ ls 
graph_org.py
organizations-state.png
```
For example:

![Organizations Diagram](./docs/images/organizations-state-copy.png)

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

