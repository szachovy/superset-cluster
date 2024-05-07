#!/bin/bash

cd setup
terraform init
terraform apply --auto-approve
cd ..

cd testsuite
ansible-playbook --inventory inventory.yml deploy.yml
