![Tests](https://github.com/szachovy/superset-cluster/actions/workflows/tests.yml/badge.svg)
![Style](https://github.com/szachovy/superset-cluster/actions/workflows/style.yml/badge.svg)

# superset-cluster

Resilent Business Intelligence.

* Survives multiple node failures with recovery mechanisms

![Demo](docs/demo.gif)

![Architecture](docs/arch.svg)

## Requirements

### Hosts specification

* Images are built and tested specifically for `Ubuntu 22.04 x86_64` Linux platforms shipped with `Python 3.10.12`.
* Both `ssh` and `docker` services on the nodes must be enabled by default.
* Nodes must be able to resolve DNS names between each other and be able to freely comunicate between each other in the internal network, only `443` port in the management nodes should be exposed.
* The user's host must be able to `ssh` to each of the nodes passwordlessly.
* Ability to read/write to the `/opt` directory on the nodes.
* There should be at least one available and running network interface capable of sending and receiving packets between the user's host and management nodes via IPv4, IPv6 on this interface should be disabled or made non-routable default.

### Installed software

The following software needs to be installed on the user's host:
...

The following software needs to be installed on the external nodes:

* `ca-certificates v20230311ubuntu0.22.04.1`
* `containerd.io v1.6.31-1`
* `curl v7.81.0-1ubuntu1.16`
* `docker-buildx-plugin v0.14.0-1~ubuntu.22.04~jammy`
* `docker-ce v5:26.1.0-1~ubuntu.22.04~jammy`
* `docker-ce-cli v5:26.1.0-1~ubuntu.22.04~jammy`
* `openssh-server v1:8.9p1-3ubuntu0.10`

...python packages... docker paramiko PYTHON VERSION IMPORTANT DUE TO MAGIC NUMBER

## Usage

Having two management nodes setup and three mysql nodes setup, run `./superset-cluster` with virtual ip address set to connect to on the specified network interface with a mask on the default gateway to be used as an example:

```bash
./superset-cluster \
  --mgmt-nodes node1,node2 \
  --mysql-nodes node3,node4,node5 \
  --virtual-ip-address 192.168.1.100 \
  --virtual-network-interface eth0 \
  --virtual-network-mask 24
```

Follow `./superset-cluster --help` for more information.

Next, navigate to https://192.168.1.100 in your web browser with the IP address provided in the installation to the default credentials username: superset, password: cluster
Remember to change default credentials after successful log in the Settings > Info > Reset my password

## Development

For development purposes you can setup Terraform testing infrastructure being in `./tests/setup`, run:

```bash
terraform init
terraform apply
```

Consequently, run [Usage](#usage) command against this infrastructure. For default parameters it would be:

```bash
./superset-cluster \
  --mgmt-nodes node-0,node-1 \
  --mysql-nodes node-2,node-3,node-4 \
  --virtual-ip-address 172.18.0.10 \
  --virtual-network-interface eth0 \
  --virtual-network-mask 16
```

Please refer to [the testing guide](tests/TESTING.md) for more information.

## License

[Apache v2.0](LICENSE)

## Contributing

If you notice anything missing, spot a bug, or have an enhancement proposal, feel free to open an issue with the appropriate label. Pull requests are welcome. Please ensure that the tests are updated as necessary.

## Personal contact information

In case of any inquiries, please write to email: wjmaj98@gmail.com

## Additional resources

* [What is Apache Superset?](https://superset.apache.org/docs/intro)
* [Chapter 23 InnoDB Cluster](https://dev.mysql.com/doc/refman/8.0/en/mysql-innodb-cluster-introduction.html)
* [Redis OSS and Stack](https://redis.io/docs/latest/operate/oss_and_stack/)
* [NGINX Reverse Proxy](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
