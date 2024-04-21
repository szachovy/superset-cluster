# `superset-cluster`

Apache Superset against MySQL InnoDB cluster.

## Requirements

### Installed software

The following software needs to be installed on both the user's host and external nodes. The setup has been manually tested on the following versions:

* [`docker v26.0.2, build 3c863ff`](https://www.docker.com/)


## Installation & Usage

With the [Requirements](#requirements) satisfied, you can build and run the entire setup from the repository root catalog:

```bash
./run.sh
```

Explore [docs](docs/) for further information about the setup, or visit [additional resources](#additional-resources) to learn more about Superset and MySQL components as a whole.

## Examples

### Development

```bash
./run.sh
```

## License

[Apache v2.0](LICENSE)

## Contributing

If you notice anything missing, spot a bug, or have an enhancement proposal, feel free to open an issue with the appropriate label. Pull requests are welcome. Please ensure that the tests are updated as necessary.

This is a private project and is not affiliated with SUSE. 

## Additional resources

* [What is Apache Superset?](https://superset.apache.org/docs/intro)
* [Chapter 23 InnoDB Cluster](https://dev.mysql.com/doc/refman/8.0/en/mysql-innodb-cluster-introduction.html)
* [Redis OSS and Stack](https://redis.io/docs/latest/operate/oss_and_stack/)
