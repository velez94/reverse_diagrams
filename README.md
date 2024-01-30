<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  

- [Reverse Diagrams](#reverse-diagrams)
- [Install](#install)
- [Use](#use)
    - [Requirement](#requirement)
    - [Service supported](#service-supported)
      - [AWS Organizations](#aws-organizations)
      - [Identity and Access Manager Center (SSO)](#identity-and-access-manager-center-sso)
  - [Additional Commands](#additional-commands)
    - [Combine the options](#combine-the-options)
  - [Extras](#extras)
    - [Enable autocomplete](#enable-autocomplete)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Reverse Diagrams

> Continuous Documentation Tool - Documentation as Code Tool

This package create reverse diagrams  based on your current state in your cloud environment.

# Install 

`pip install reverse-diagrams`

# Use

The following are the available options

```commandline
$  reverse_diagrams -h 
usage: reverse_diagrams [-h] [-p PROFILE] [-od OUTPUT_DIR_PATH] [-r REGION] [-o] [-i] [-a] [-v] [-d]

options:
  -h, --help            show this help message and exit
  -p PROFILE, --profile PROFILE
                        AWS cli profile for AWS Apis
  -od OUTPUT_DIR_PATH, --output_dir_path OUTPUT_DIR_PATH
                        Name of folder to save the diagrams python code files
  -r REGION, --region REGION
                        AWS region
  -o, --graph_organization
                        Set if you want to create graph for your organization
  -i, --graph_identity  Set if you want to create graph for your IAM Center
  -a, --auto_create     Create Automatically diagrams
  -v, --version         Show version
  -d, --debug           Debug Mode

```
For example: 

```commandline
reverse_diagrams -p labvel-master -o -i -r us-east-1

❇️ Describe Organization 
❇️ Getting Organization Info
❇️ Listing Organizational Units 
❇️ Getting the Account list info
ℹ️  There are 11 Accounts in your organization
ℹ️  The accounts are stored in diagrams/json/organizations.json 
❇️ Creating diagrams in diagrams/code
❇️ Getting Identity store instance info
❇️ List groups
ℹ️  There are 10 Groups in your Identity Store
❇️ Get groups and Users info
Getting groups members... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:07
Getting account assignments ... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:05:23
Create user and groups assignments ... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00
❇️ Getting account assignments, users and groups
ℹ️  The accounts are stored in diagrams/json/account_assignments.json
ℹ️  The accounts are stored in diagrams/json/groups.json
❇️ Creating diagrams in diagrams/code

```
Then run `python3 graph_org.py` to create a png screenshot (`organizations-state.png`) for your current state.

> Both files are saved into the current directory.

```commandline
$  reverse_diagrams -p labvel-master -o -r us-east-2
Date: 2022-12-17 22:44:07.623260
❇️ Getting Organization Info
❇️ The Organizational Units list 
❇️ Getting the Account list info
Run -> python3 graph_org.py 


$ python3 graph_org.py 
$ ls 
graph_org.py
organizations-state.png
```
For example:

![Organizations Diagram](./docs/images/organizations-state-copy.png)

Now you can edit `graph_org.py` file or add to your repositories for keeping the documentation update.

### Requirement

AWS programmatic access using AWS CLI. :arrow_right: [Configuring the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)

### Service supported

#### AWS Organizations

```commandline
reverse_diagrams -c aws -p my-profile -o -r us-east-2
```
#### Identity and Access Manager Center (SSO)

```commandline
reverse_diagrams -c aws -p my-profile -i -r us-east-2
```
## Additional Commands

### Combine the options

```commandline
reverse_diagrams -c aws -p my-profile -o -i -r us-east-2
```

## Extras
### Enable autocomplete
Argcomplete provides easy, extensible command line tab completion of arguments for your Python application.

It makes two assumptions:

* You’re using bash or zsh as your shell

* You’re using argparse to manage your command line arguments/options

Argcomplete is particularly useful if your program has lots of options or subparsers, and if your program can dynamically suggest completions for your argument/option values (for example, if the user is browsing resources over the network).
Run: 
```bash
activate-global-python-argcomplete
```
and to make sure that bash knows about this script, you use
```bash

echo 'eval "$(register-python-argcomplete reverse_diagrams)"' >> ~/.bashrc
source ~/.bashrc

```