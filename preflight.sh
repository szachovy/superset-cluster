#!/bin/bash

set -euo pipefail

PASS=0
FAIL=0

check() {
    local name="$1"
    local cmd="$2"
    local hint="${3:-}"
    if eval "$cmd" > /dev/null 2>&1; then
        echo "  [PASS] ${name}"
        PASS=$((PASS + 1))
    else
        echo "  [FAIL] ${name}"
        [ -n "${hint}" ] && echo "         Hint: ${hint}"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== superset-cluster pre-flight checks ==="
echo

check "Python 3.10+" \
    "python3 --version 2>&1 | grep -qE 'Python 3\.(1[0-9]|[2-9][0-9])'" \
    "Install Python 3.10+: sudo apt install python3 or use pyenv"

check "Docker daemon" \
    "docker info" \
    "Install Docker: https://docs.docker.com/engine/install/"

check "Docker socket" \
    "test -S /var/run/docker.sock" \
    "Ensure Docker daemon is running: sudo systemctl start docker"

check "docker group membership" \
    "groups | grep -q docker" \
    "Add user to docker group: sudo usermod -aG docker \$USER && newgrp docker"

check "Terraform" \
    "terraform version" \
    "Install Terraform: https://developer.hashicorp.com/terraform/install"

check "Ansible" \
    "ansible --version" \
    "Install Ansible: pip install ansible"

check "SSH client" \
    "ssh -V 2>&1" \
    "Install OpenSSH: sudo apt install openssh-client"

echo
echo "Results: ${PASS} passed, ${FAIL} failed"
[ "${FAIL}" -eq 0 ] || exit 1
