![badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/szachovy/d4fd269e226b0ed70954f861129a2756/raw/superset-cluster-codecoverage.json)

# superset-cluster

Apache Superset against MySQL InnoDB cluster.
[That's how it works](docs/ARCHITECTURE.md).

## Requirements

### Hosts specification

* Images are built specifically for `x86_64` or `arm64` Linux platforms shipped with Python 3.
* Both `ssh` and `docker` services on the nodes must be enabled by default.
_[See how to do it with `systemctl`](https://documentation.suse.com/smart/systems-management/html/reference-systemctl-enable-disable-services/index.html#id-1.4)._
* Nodes must be able to resolve DNS names between each other.
* The user's host must be able to `ssh` to each of the nodes passwordlessly.
* There should be at least one available and running network interface capable of sending and receiving packets between the user's host and management nodes via IPv4.
* Ability to read/write to the `/opt` directory on the nodes.
* On the MySQL nodes port `3306` should be open for communication within the nodes.
* On the Management nodes port `6446` should be open for communication within the nodes.
* For production setups follow [SECURITY.md](docs/SECURITY.md).

### Installed software

The following software needs to be installed on both the user's host and external nodes. The setup has been tested on [`ubuntu:22.04`](tests/setup/Dockerfile) with the following versions:

* `ca-certificates v20230311ubuntu0.22.04.1`
* `containerd.io v1.6.31-1`
* `curl v7.81.0-1ubuntu1.16`
* `docker-buildx-plugin v0.14.0-1~ubuntu.22.04~jammy`
* `docker-ce v5:26.1.0-1~ubuntu.22.04~jammy`
* `docker-ce-cli v5:26.1.0-1~ubuntu.22.04~jammy`
* `openssh-server v1:8.9p1-3ubuntu0.7`

## Installation & Usage

With the [Requirements](#requirements) satisfied, you can build and run the entire setup from the repository root catalog:

```bash
./run.sh
```

Explore [docs](docs/) for further information about the setup, or visit [additional resources](#additional-resources) to learn more about Superset and MySQL components as a whole.

### Example

Having the `tun0` network interface on the localhost that enables connections to the hosts available for the management nodes with the following addresses:
* `10.145.211.151`
* `10.145.211.152`

With hosts available for the MySQL InnoDB cluster having the following addresses:
* `10.145.211.153`
* `10.145.211.154`
* `10.145.211.156`

The exemplary command for execution is as follows:

```bash
./run.sh \
  --network-interface=tun0 \
  --mgmt-nodes=10.145.211.151,10.145.211.152 \
  --mysql-nodes=10.145.211.153,10.145.211.154,10.145.211.156
```

### Development

For development purposes, you can set up and run end-to-end tests from the test suite locally. Testing infrastructure remains preserved. Please refer to [the testing guide](tests/TESTING.md) for more information.

## License

[Apache v2.0](LICENSE)

## Contributing

If you notice anything missing, spot a bug, or have an enhancement proposal, feel free to open an issue with the appropriate label. Pull requests are welcome. Please ensure that the tests are updated as necessary.

## Additional resources

* [What is Apache Superset?](https://superset.apache.org/docs/intro)
* [Chapter 23 InnoDB Cluster](https://dev.mysql.com/doc/refman/8.0/en/mysql-innodb-cluster-introduction.html)
* [Redis OSS and Stack](https://redis.io/docs/latest/operate/oss_and_stack/)
