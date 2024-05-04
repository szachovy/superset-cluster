#!/bin/bash

ssh-keygen -t rsa -b 2048 -f id_rsa -N ''
chmod 600 id_rsa.pub
ssh-add id_rsa
echo "StrictHostKeyChecking no" | sudo tee --append "/etc/ssh/ssh_config"

apt update && apt install inetutils-ping