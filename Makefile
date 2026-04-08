.PHONY: setup test teardown clean

setup:
	cd tests/setup && terraform init && terraform apply -auto-approve

test: setup
	cd tests/testsuite && ansible-playbook --inventory inventory.yml deploy.yml

teardown:
	cd tests/setup && terraform destroy -auto-approve

clean: teardown
	docker volume prune --force
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
