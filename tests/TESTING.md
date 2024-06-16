# Testing

Main tests catalog of `superset-cluster`.

## Testing objectives and procedures

Testing consist of two modules:
* `setup`: Generates / makes changes in files (see [SECURITY.md](../docs/SECURITY.md)), and sets up Terraform infrastructure which typically consist of 5 docker containers imitating standalone nodes from the [architecture](../docs/ARCHITECTURE.md), where:
  * `<node-prefix>-0` is the primary management node
  * `<node-prefix>-1` is the primary mysql node
  * `<node-prefix>-2` is the secondary mysql node
  * `<node-prefix>-3` is the secondary mysql node
  * `<node-prefix>-4` is the superset node
  ...
* `testsuite`: Ansible playbook running testsuite against applied terraform infrastructure, that include:
  * [Infrastructure](testsuite/roles/testing/tasks/infrastructure.yml) tests: Conditional checks if the [requirements](../README.md#requirements) of generated infrastructure are meet.
  * [System](testsuite/roles/testing/tasks/system.yml) tests: Simulated end-to-end deployment process of `superset-cluster` against terraform generated infrastructure instead of user provided hosts.
  * [Functional](testsuite/roles/testing/tasks/functional.yml) tests: ... meet the requirements for the end user ...

## Running tests

### Host requirements

Tests would fail if the host system is unable to hold 5 <...> containers running in parallel.
It has been tested on: ...
<RAM> ...

### Required software

Testing host is the `ubuntu:22.04` and has the following software installed:

* `terraform v1.0.10`
* `openssh-server v1:8.9p1-3ubuntu0.7`
* `python v3.10.12` with the following third party packages:
  * `ansible v9.5.1`
  * `docker v5.0.3`
  * `requests v2.25.1`

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

...

### Ansible variables

Ansible group variables is a dynamically modified file consisting of pre-populated [defaults](../src/defaults.yml), shared values from [Terraform variables](#terraform-variables) and dynamically generated passwords for testing:

...

## Automated testing

...github CI

### Additional resources

* [Terraform Docker provider](https://registry.terraform.io/providers/kreuzwerker/docker/latest/docs)
* [Ansible Community Docker](https://docs.ansible.com/ansible/latest/collections/community/docker/index.html)
* [Superset API](https://superset.apache.org/docs/api/#api)
