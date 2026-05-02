# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

* [PERFORMANCE.md](./docs/PERFORMANCE.md), [SECURITY.md](./docs/SECURITY.md) and
  [RELIABILITY.md](./docs/RELIABILITY.md) documents in the documentation. (#93)
* CodeQL code scanning workflow for Python static analysis. (#29)
* Dependabot updates for `github-actions` and `terraform` ecosystems. (#29)
* CI workflow to build and push service images to GitHub Container Registry on master merge. (#97)
* Pull-first with local build fallback for container images during deployment. (#97)
* `--cleanup` CLI flag with idempotent deploy and cleanup actions. (#49)
* Credential recovery for partial redeploy from existing healthy nodes. (#49)
* PEM serialization support in `crypto.py` for credential recovery. (#49)
* InnoDB Cluster auto-join for fresh MySQL nodes added to an existing cluster. (#49)
* Disaster recovery test flow with node replacement and partial redeploy verification. (#49)
* Swarm overlay network encryption via IPsec and explicit data path port. (#92)
* MySQL slow query log for queries exceeding 10 seconds or not using indexes. (#76)
* Strengthen MySQL superset password: secrets module, expanded charset, 24 chars. (#89)
* SQL Lab query row limits, timeout caps, and validation timeout. (#81)
* Superset metastore and explore form data caching via Redis. (#79)

### Changed

* Completed [ARCHITECTURE.md](./docs/ARCHITECTURE.md) (#93)
* Migrated CI from self-hosted to GitHub-hosted runners with Docker-in-Docker test infrastructure. (#94)
* Test workflow always builds service images locally for reproducibility. (#97)
* Restructured test suite into 10-stage flow: sanity, deploy, functional, disaster, post-disaster,
  recovery, redeploy, post-redeploy functional, cleanup, cleanup verification. (#49)
* InnoDB Cluster initcontainer scans all MySQL nodes to find existing cluster and adds missing
  members instead of only checking the primary node. (#49)
* Made Terraform test infrastructure idempotent: removed `always_run` triggers, node recovery
  reruns `terraform apply` which only recreates missing containers. (#49)
* Enabled parallel replication applier threads on secondary MySQL nodes. (#75)
* Clean up temporary `.pyc` files on remote nodes after execution. (#51)
* Set `innodb_flush_method=O_DIRECT` to eliminate double caching in containers. (#74)
* Reduced InnoDB change buffer size for read-heavy BI workload. (#72)
* Set InnoDB buffer pool size to 1G for improved query performance. (#71)
* Relaxed Terraform version constraint to accept any 1.x release. (#40)

### Removed

* Removed personal contact section from README. (#159)

### Fixed

* Upload `.py` source instead of `.pyc` bytecode to decouple host Python version. (#38, #41)
* Fixed `run_mysql_server()` not instantiating `MySQLServer` class. (#94)
* Disabled MD060 markdownlint rule to fix table column style false positives in documentation. (#94)
* Made `create_directory()` idempotent to support deployment re-runs. (#35)
* Added default inventory directive to `ansible.cfg`. (#42)
* Fixed Publish workflow `write_package` permission denied by adding OCI source labels for GHCR repository linking. (#99)
* Restore `pipefail` in Tests workflow to propagate non-zero exit codes through pipes. (#160)

## 1.0 - 2024-10-13

### Added

* Initial implementation of the project's defined structure. (#1)
* Tests structure. (#7)
* Credentials management. (#6) (#16)
* Management node in high availability. (#11)
* Transport Layer Security. (#14)
* Superset automations with Nginx. (#5) (#16)
* CLI argparsing with common Python logic. (#3)
* Collective style improval. (#22)

[Unreleased]: https://github.com/szachovy/superset-cluster/compare/1.0...master
