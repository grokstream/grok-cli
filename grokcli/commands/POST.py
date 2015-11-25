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
from optparse import OptionParser
from urlparse import urlparse
import grokcli
from grokcli.api import GrokSession, Response
from functools import partial
import select
import sys

# Subcommand CLI Options

if __name__ == "__main__":
  subCommand = "%prog"
else:
  subCommand = "%%prog %s" % __name__.rpartition('.')[2]

USAGE = """%s GROK_URL GROK_API_KEY [options]

""".strip() % subCommand

parser = OptionParser(usage=USAGE)
parser.add_option(
  "-d",
  "--data",
  dest="data",
  metavar="FILE or -",
  help="Path to file containing request data, or - if you want to " \
       "read the data from stdin.")

# Implementation

def handle(options, args):
  """ `grok POST` handler. """
  (endpoint, apikey) = grokcli.getCommonArgs(parser, args)

  if options.data:
    data = options.data
  else:
    # Pop data source off args
    try:
      data = args.pop(0)
    except IndexError:
      data = ""

  server = "%(scheme)s://%(netloc)s" % urlparse(endpoint)._asdict()

  grok = GrokSession(server=server, apikey=apikey)

  post = partial(grok.post, endpoint)

  response = None
  if data.strip() == "-" or not data:
    if select.select([sys.stdin,],[],[],0.0)[0]:
      response = post(data=sys.stdin)
    else:
      response = post()
  elif data:
    with open(data, "r") as fp:
      response = post(data=fp)

  if isinstance(response, Response):
    print response.text
    sys.exit(not int(bool(response)))


if __name__ == "__main__":
  handle(*parser.parse_args())
