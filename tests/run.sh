#!/bin/bash

cd setup
terraform init
terraform apply --auto-approve
cd ..

./testsuite/end-to-end.sh
