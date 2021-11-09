#!/usr/bin/python
# Copyright (c) 2021 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
module: postgresql_ping_db.py
short_description: Test connection to a PostgreSQL Database instance.
description:
    - This module connect to a database instance.
author: 'Aubin Bikouo (@abikouo)'
options:
  host:
    description:
      - fully qualified name of the PostgreSQL Server.
    required: true
    type: str
  dbname:
    description:
      - Database name.
    required: true
    type: str
  user:
    description:
      - username.
    required: true
    type: str
  password:
    description:
      - password.
    required: true
    type: str

requirements:
  - psycopg2
'''

EXAMPLES = '''
- name: Ping a simple PostgreSQL database
  postgresql_ping_db:
    host: "ansible-postgresql-00.postgres.database.azure.com"
    dbname: "db-00"
    user: "ansible@ansible-postgresql-00"
    password: "test123!"
'''

RETURN = '''
'''

HAS_PSYCOPG2 = None
try:
    from psycopg2 import connect
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = dict(
        host=dict(required=True),
        dbname=dict(required=True),
        user=dict(required=True),
        password=dict(required=True, no_log=True),
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_PSYCOPG2:
        module.fail_json(msg="This module requires psycopg2 module.")

    conn_string = "host={0} user={1} dbname={2} password={3} sslmode='require'".format(module.params.get('host'),
                                                                                       module.params.get('user'),
                                                                                       module.params.get('dbname'),
                                                                                       module.params.get('password'))
    try:
        conn = connect(conn_string)
        conn.close()
        module.exit_json(changed=False, msg="Connection established.")
    except Exception as e:
        module.fail_json(msg="Connection failed due to: {0}".format(e))

if __name__ == '__main__':
    main()
