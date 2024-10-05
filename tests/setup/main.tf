terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "3.0.2"
    }
  }
}

provider "docker" {
  host = "unix:///var/run/docker.sock"
}

resource "null_resource" "manage_ssh" {
  triggers = {
    always_run = "${timestamp()}"
  }

  provisioner "local-exec" {
    when    = create
    command = <<-EOT
      ssh-keygen -t rsa -b 2048 -f id_rsa -N ''
      chmod 600 id_rsa.pub
      [ -f $HOME/.ssh/config ] || mkdir --parents $HOME/.ssh && touch $HOME/.ssh/config
      echo "### Terraform autogenerated content start ###" >> $HOME/.ssh/config
    EOT
  }

  provisioner "local-exec" {
    when    = destroy
    command = <<-EOT
      rm id_rsa id_rsa.pub
      sed --in-place \
        "/### Terraform autogenerated content start ###/,\
        /### Terraform autogenerated content end ###/d" \
        $HOME/.ssh/config
    EOT
  }
}

resource "docker_network" "nodes_network" {
  name = "${var.node_prefix}-network"

  ipam_config {
    subnet  = var.subnet
    gateway = var.gateway
  }

  labels {
    label = "app"
    value = "superset-cluster"
  }
}

resource "docker_image" "node_image" {
  name = "${var.node_prefix}:${var.node_version}"

  triggers = {
    always_run = "${timestamp()}"
  }

  build {
    context = "."

    labels = {
      label = "app"
      value = "superset-cluster"
    }
  }

  depends_on = [
    null_resource.manage_ssh
  ]
}

resource "docker_container" "nodes" {
  count      = "5"
  name       = "${var.node_prefix}-${count.index}"
  hostname   = "${var.node_prefix}-${count.index}"
  image      = docker_image.node_image.name
  privileged = true  # nodes containers are treated as standalone virtual machines

  ports {
    internal = 8088
    external = 8088 + count.index
  }

  ulimit {
    name = "nofile"
    soft = 1024
    hard = 65535
  }

  networks_advanced {
    name         = docker_network.nodes_network.name
    ipv4_address = cidrhost("${var.subnet}", "${2 + count.index}")
  }

  labels {
    label = "app"
    value = "superset-cluster"
  }

  provisioner "local-exec" {
    command = <<-EOT
      docker cp ../../src $HOSTNAME:/opt/superset-testing
      docker cp ../../services/mysql-mgmt/interfaces.py $HOSTNAME:/opt/superset-testing
      docker cp ../testsuite/roles/testing/files/. $HOSTNAME:/opt/superset-testing
      docker exec $HOSTNAME /bin/bash -c \
        "wget --directory-prefix=/tmp --quiet https://bootstrap.pypa.io/get-pip.py \
        && python3 /tmp/get-pip.py > /dev/null 2>&1 \
        && python3 -m pip install --quiet --no-cache-dir --user --requirement /opt/superset-testing/requirements.txt"
      docker exec --user=root $HOSTNAME /bin/bash -c \
        "service ssh start \
        && service docker start \
        && echo -e 'nameserver 8.8.8.8\nnameserver 8.8.4.4' >> /etc/resolv.conf \
        && usermod --append --groups docker superset \
        && chown --recursive superset:superset /opt/superset-testing"
      echo "Host $HOSTNAME
        Hostname $IP_ADDRESS
        StrictHostKeyChecking no
        IdentityFile $(pwd)/id_rsa
        IdentitiesOnly yes" >> $HOME/.ssh/config
    EOT

    environment = {
      HOSTNAME   = "${var.node_prefix}-${count.index}"
      IP_ADDRESS = cidrhost("${var.subnet}", "${2 + count.index}")
    }
  }

  depends_on = [
    docker_image.node_image,
    docker_network.nodes_network,
    null_resource.manage_ssh
  ]
}

resource "null_resource" "generate_ansible_group_vars" {
  triggers = {
    always_run = "${timestamp()}"
  }

  provisioner "local-exec" {
    when    = create
    command = <<-EOT
      mkdir $(dirname $GROUP_VARS_FILE)
      {
        echo "virtual_ip_address: \"$VIRTUAL_IP_ADDRESS\""
        echo "virtual_network_mask: \"$VIRTUAL_NETWORK_MASK\""
        echo "node_prefix: \"$NODE_PREFIX\""
      } > $GROUP_VARS_FILE
    EOT

    environment = {
      GROUP_VARS_FILE         = "../testsuite/group_vars/testing.yml"
      NODE_PREFIX             = "${var.node_prefix}"
      VIRTUAL_IP_ADDRESS      = cidrhost("${var.subnet}", "${10}")
      VIRTUAL_NETWORK_MASK = cidrnetmask("${var.subnet}")
    }
  }

  provisioner "local-exec" {
    when    = destroy
    command = "rm --recursive $(dirname $GROUP_VARS_FILE)"

    environment = {
      GROUP_VARS_FILE = "../testsuite/group_vars/testing.yml"
    }
  }
}

resource "null_resource" "finish_configuration" {
  triggers = {
    always_run = "${timestamp()}"
  }

  provisioner "local-exec" {
    command = <<-EOT
      echo "### Terraform autogenerated content end ###" >> $HOME/.ssh/config
    EOT
  }

  depends_on = [
    docker_container.nodes
  ]
}
