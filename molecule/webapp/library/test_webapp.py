#!/usr/bin/python
# Copyright (c) 2021 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = '''
module: test_webapp.py
short_description: Test application is running and provide usefull information.
description:
    - Test if the load balancer is working as expected.
author: 'Aubin Bikouo (@abikouo)'
options:
  url:
    description:
      - application url.
    required: true
    type: str
  number_workers:
    description:
      - number of workers on the load balancer pool.
    type: int

requirements:
  - requests
  - html.parser
'''

EXAMPLES = '''
'''

RETURN = '''
'''

from ansible.module_utils.basic import AnsibleModule  # noqa: E402
import requests  # noqa: E402
import re  # noqa: E402
from html.parser import HTMLParser  # noqa: E402


class htmlParser(HTMLParser):
    def __init__(self):
        self.workers = None
        self.hit = None

        super(htmlParser, self).__init__()

    def handle_data(self, data):
        if data == "Workers":
            self.workers = []
        elif re.match("[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+", data):  # noqa: W605
            if self.workers is not None:
                self.workers.append(data)
            else:
                self.hit = data


def ping_application(module):
    url = "%s/display" % module.params.get('url')
    ret = requests.get(url)
    if ret.status_code != 200:
        msg = "Application not reachable,"\
              "requests return status code {0}".format(ret.status_code)
        module.fail_json(msg=msg)

    parser = htmlParser()
    parser.feed(ret.text)

    return parser.hit, parser.workers


def test_load_balancer(module):

    nb_workers = module.params.get('number_workers')
    hits = []
    for i in range(2 * nb_workers):
        hit, workers = ping_application(module)
        if hit not in hits:
            hits.append(hit)

    if len(hits) != nb_workers:
        msg = "{} Workers expected, but only {} Workers"\
              " found from load balancer pool".format(nb_workers, len(hits))
        module.fail_json(msg=msg)

    module.exit_json(msg="{} Workers found as expected".format(len(hits)))


def main():
    argument_spec = dict(
        url=dict(required=True),
        number_workers=dict(type='int'),
    )

    module = AnsibleModule(argument_spec=argument_spec)

    try:
        test_load_balancer(module)
    except Exception as e:
        module.fail_json(msg="raised: {0}".format(e))


if __name__ == '__main__':
    main()
