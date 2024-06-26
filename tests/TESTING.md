# Testing

Main tests catalog of `superset-cluster`.

## Testing objectives and procedures

Testing consist of two modules:

### `setup`

* Generates `id_rsa` and `id_rsa.pub` keys on the user's host under `setup/` directory and adds them to ssh agent
* Adds records to `$HOME/.ssh/config`
* Creates `testing.yml` group variables for the testsuite
* Sets up Terraform infrastructure which consist of 5 docker containers imitating standalone nodes, where:
  * `<node-prefix>-0` is the primary management node
  * `<node-prefix>-1` is the primary mysql node
  * `<node-prefix>-2` is the secondary mysql node
  * `<node-prefix>-3` is the secondary mysql node
  * `<node-prefix>-4` is the superset node

### `testsuite`

Ansible playbook running testsuite against applied terraform infrastructure, that include:
* [Infrastructure](testsuite/roles/testing/tasks/infrastructure.yml) tests: Conditional checks if the [requirements](../README.md#requirements) of generated infrastructure are meet.
* [System](testsuite/roles/testing/tasks/system.yml) tests: Simulated end-to-end deployment process of `superset-cluster` against terraform generated infrastructure instead of user provided hosts.
* [Functional](testsuite/roles/testing/tasks/functional.yml) tests: Verifying end-user primary usage cases in pipelines of superset and management node component functions

## Running tests

### Required software

Testing host is the `ubuntu:22.04` runner with the [software installed](../README.md#installed-software) meeting the [required criteria](../README.md/#hosts-specification) with the following software installed for testing:

* `terraform v1.0.10`
* `python v3.10.12` with the following third party packages:
  * `ansible v9.5.1`

Testing does not require any additional modules on the terraform initiated infrastructure, current versions of deployed software has been described in the project's [`README.md`](../README.md/#installed-software).

### Usage

Being in the `setup` catalog run `terraform` commands to initialize infrastructure:

```
terraform init
terraform apply --auto-approve
```

After successful run, and 5 docker containers appeared with a healthy state, run ansible playbook while being in the `testsuite` catalog to start tests:

```
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

### Ansible variables

Ansible group variables is a dynamically modified file consisting of pre-populated [defaults.yml](../src/defaults.yml), [variables.tf](./setup/variables.tf) and auto-generated passwords for testing:

| Variable Name                     | Origin                                 |
|-----------------------------------|----------------------------------------|
| `celery_broker`                   | [defaults.yml](../src/defaults.yml)    |
| `celery_sql_lab_task_annotations` | [defaults.yml](../src/defaults.yml)    |
| `database_name`                   | [defaults.yml](../src/defaults.yml)    |
| `mgmt_hostname`                   | [defaults.yml](../src/defaults.yml)    |
| `mysql_password`                  | Auto-generated                         |
| `mysql_user`                      | [defaults.yml](../src/defaults.yml)    |
| `network_interface`               | [defaults.yml](../src/defaults.yml)    |
| `node_prefix`                     | [variables.tf](./setup/variables.tf)   |
| `redis_hostname`                  | [defaults.yml](../src/defaults.yml)    |
| `redis_port`                      | [defaults.yml](../src/defaults.yml)    |
| `superset_hostname`               | [defaults.yml](../src/defaults.yml)    |
| `superset_password`               | Auto-generated                         |

### Additional resources

* [Terraform Docker provider](https://registry.terraform.io/providers/kreuzwerker/docker/latest/docs)
* [Ansible Community Docker](https://docs.ansible.com/ansible/latest/collections/community/docker/index.html)
* [Superset API](https://superset.apache.org/docs/api/#api)
