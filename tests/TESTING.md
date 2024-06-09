# Testing

Testing consist of two modules:
* `setup`: Sets up Terraform infrastructure which typically consist of 6 docker containers imitating standalone nodes, where:
  * `<node-prefix>-0` is ...
  ...
* `testsuite`: Ansible playbook that run testsuite against applied terraform infrastructure.

## Testing objectives and procedures

Ansible testsuite include: ...
* [Infrastructure](testsuite/roles/testing/tasks/infrastructure.yml) tests: Conditional checks if the [requirements](../README.md#requirements) of generated infrastructure are meet.
* [System](testsuite/roles/testing/tasks/system.yml) tests: Simulated end-to-end deployment process of `superset-cluster` against terraform generated infrastructure instead of user provided hosts.
* [Functional](testsuite/roles/testing/tasks/functional.yml) tests: ... meet the requirements for the end user ...

## Running tests

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

After successfull run, and 5 docker containers appeared with a healthy state, populate terraform variables and project's defaults to the ansible group variables by running the script from the `tests` directory:

```
./generate_group_vars.sh
```

To execute testsuite, run ansible playbook while being in the `testsuite` catalog:

```
ansible-playbook --inventory inventory.yml deploy.yml
```

## Defaults

Some of the variables are shared between [terraform variables](./setup/variables.tf) and 

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
