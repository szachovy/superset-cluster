#!/bin/bash

container_ids=$(docker ps -a --filter "name=pi-*" -q)

if [ -n "$container_ids" ]; then
    for container_id in $container_ids; do
        echo "Removing container: $container_id"
        docker stop "$container_id" >/dev/null 2>&1
        docker rm "$container_id" >/dev/null 2>&1
    done
else
    echo "No containers with names starting with 'pi-' found."
fi

number_of_containers="${1}"
if [ ! -f id_rsa ]; then
    ssh-keygen -t rsa -b 2048 -f id_rsa -N ""
    ssh-add id_rsa
fi
docker build -t raspberry-pi-container .

for ((i = 0; i < number_of_containers; i++)); do
    container_name="pi-${i}"
    docker run -d --name "pi-${i}" -p "$((2222+${i})):22" raspberry-pi-container
    docker cp id_rsa.pub "pi-${i}":/root/.ssh/id_rsa.pub
    docker exec -u root "pi-${i}" sh -c 'cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys'
done
