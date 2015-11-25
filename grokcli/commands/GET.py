#!/usr/bin/env python
#------------------------------------------------------------------------------
# Copyright 2013-2014 Avik Partners, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#------------------------------------------------------------------------------
import sys
from optparse import OptionParser
from urlparse import urlparse
import grokcli
from grokcli.api import GrokSession, Response



# Subcommand CLI Options

if __name__ == "__main__":
  subCommand = "%prog"
else:
  subCommand = "%%prog %s" % __name__.rpartition('.')[2]

USAGE = """%s GROK_URL GROK_API_KEY [options]

""".strip() % subCommand

parser = OptionParser(usage=USAGE)
try:
  import yaml
  parser.add_option(
    "-y",
    "--yaml",
    dest="useYaml",
    default=False,
    action="store_true",
    help="Display results in YAML format")
except ImportError:
  pass # yaml not available, hide from user

# Implementation

def handle(options, args):
  """ `grok GET` handler. """
  (endpoint, apikey) = grokcli.getCommonArgs(parser, args)

  server = "%(scheme)s://%(netloc)s" % urlparse(endpoint)._asdict()

  grok = GrokSession(server=server, apikey=apikey)

  response = grok.get(endpoint)

  if isinstance(response, Response):
    if hasattr(options, "useYaml"):
      if options.useYaml:
        print yaml.safe_dump(yaml.load(response.text), default_flow_style=False)
      else:
        print response.text

    sys.exit(not int(bool(response)))


if __name__ == "__main__":
  handle(*parser.parse_args())
