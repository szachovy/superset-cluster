# Testing

Testing consist of two modules:
* `setup` sets up Terraform infrastructure which typically consist of `n` number of docker containers imitating standalone nodes
* `testsuite` - ansible playbook that run testsuite against applied terraform infrastructure

## Testing objectives and procedures

* [Infrastructure](testsuite/roles/testing/tasks/infrastructure.yml) tests
  * ...conditional checks if the [requirements](../README.md#requirements) of generated infrastructure are meet.
* [System](testsuite/roles/testing/tasks/system.yml) tests
  * ...trying to mimic the same deployment process, but against terraform generated infrastructure instead of user provided hosts
* [Functional](testsuite/roles/testing/tasks/functional.yml) tests
  * ...
* [Performance](testsuite/roles/testing/tasks/performance.yml) tests
  * ...

## Running tests

### Required sotfware

### Default ...

```bash
run.sh
```

### Variables

...

## Automated testing

...github CI

### Additional resources

* [Terraform Docker provider](https://registry.terraform.io/providers/kreuzwerker/docker/latest/docs)
