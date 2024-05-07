# Testing

Testing consist of two modules:
* `setup` sets up Terraform infrastructure which typically consist of `n` number of docker containers imitating standalone nodes
* `testsuite` - ansible playbook that run testsuite against applied terraform infrastructure

## Testing objectives and procedures

* [System](testsuite/roles/end-to-end/tasks/system.yml) tests
  * ...
* Integration tests ...

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
