# Testing

Main tests catalog of `superset-cluster`.

## Testing objectives and procedures

Testing consist of two modules:

### `setup`

* Generates `id_rsa` and `id_rsa.pub` keys on the user's host under `setup/` directory and adds them to ssh agent
* Adds records to `$HOME/.ssh/config`
* Creates `./testsuite/group_vars/testing.yml` group variables for the testsuite
* Sets up Terraform infrastructure which consist of 5 equal docker containers imitating standalone nodes, where:
  * `<node-prefix>-0` is set as the primary management node
  * `<node-prefix>-1` is set as the secondary management node
  * `<node-prefix>-2` is set as the primary mysql node
  * `<node-prefix>-3` is set as the secondary mysql node
  * `<node-prefix>-4` is set as the secondary mysql node

### `testsuite`

Ansible playbook running testsuite against applied terraform infrastructure, that include:

* [Sanity](testsuite/roles/testing/tasks/sanity.yml) tests:
  Conditional checks if the [requirements](../README.md#requirements) of generated infrastructure are meet.
* [System](testsuite/roles/testing/tasks/system.yml) tests:
  Simulated end-to-end deployment process of `superset-cluster` against terraform generated infrastructure.
* [Functional](testsuite/roles/testing/tasks/functional.yml) tests:
  Verifying end-user primary use cases in pipelines of superset and management node component functions

## Running tests

### Required software

Testing host is the `ubuntu:22.04` runner with 1 core of AMD EPYC 7773X x86_64 CPU and 8GiB of RAM
with the [software installed](../README.md#installed-software)
meeting the [required criteria](../README.md/#hosts-specification)
with the following software installed for testing:

* `terraform v1.0.10`
* `python v3.10.12` with the following third party packages:
  * `ansible v9.5.1`

Optionally, the following software is installed for doing [style checks](https://github.com/szachovy/superset-cluster/actions):

* `pylint v3.2.4`
* `mypy v1.10.1 (compiled)`
* `flake8 v7.1.0`
* `markdownlint-cli v0.41.0`
* `shellcheck v0.8.0`
* `hadolint v2.12.2`
* `ansible-lint v24.6.1`
* `tflint v0.51.1`
* `yamllint v1.35.1`

### Usage

Navigate to the `setup` directory and execute the following
Terraform commands to initialize the infrastructure:

```bash
terraform init
terraform apply
```

Once the commands have successfully completed,
switch to the testsuite directory and run the Ansible playbook
to start the tests:

```bash
ansible-playbook --inventory inventory.yml deploy.yml
```

### Terraform variables

[Terraform variables](./setup/variables.tf) consist of singularly defined variables for a given deployed infrastructure:

| Variable Name   | Description                             | Default Value   |
|-----------------|-----------------------------------------|-----------------|
| `gateway`       | Network gateway for the container nodes | "172.18.0.1"    |
| `node_prefix`   | Prefix of the container nodes           | "node"          |
| `node_version`  | Version of the container nodes deployed | "1.0"           |
| `subnet`        | Network subnet for the container nodes  | "172.18.0.0/16" |

### Ansible Variables

Ansible group variables are dynamically defined after terraform setup within a file. The following variables are used:

| Variable Name                | Description                                 | Default Value     |
|------------------------------|---------------------------------------------|-------------------|
| `virtual_network_interface`  | Network interface for the virtual network   | "eth0"            |
| `virtual_ip_address`         | Virtual IP address assigned to the nodes    | "172.18.0.10"     |
| `virtual_network_mask`       | Network mask for the virtual network        | "255.255.0.0"     |
| `node_prefix`                | Prefix for the container nodes              | "node"            |

### Additional resources

* [Terraform Docker provider](https://registry.terraform.io/providers/kreuzwerker/docker/latest/docs)
* [Ansible Community Docker](https://docs.ansible.com/ansible/latest/collections/community/docker/index.html)
* [Superset API](https://superset.apache.org/docs/api/#api)
* [The MySQL Shell](https://dev.mysql.com/doc/mysql-shell/8.0/en/mysqlsh.html)
