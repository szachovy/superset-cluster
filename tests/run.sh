#!/bin/bash

NODES="${1}"

./setup/setup.sh ${NODES}
./run-testsuite/run.sh
