#!/usr/bin/env bash

set -eux

# Run tests
ansible-playbook playbooks/main.yml "$@"
