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
import json
from optparse import OptionParser
import sys

from prettytable import PrettyTable

import grokcli
from grokcli.api import GrokSession


if __name__ == "__main__":
  subCommand = "%prog"
else:
  subCommand = "%%prog %s" % __name__.rpartition('.')[2]

USAGE = """%s (list|unmonitor) [GROK_SERVER_URL GROK_API_KEY] [options]

Browse...
""".strip() % subCommand


parser = OptionParser(usage=USAGE)
parser.add_option(
  "--id",
  dest="id",
  metavar="ID",
  help='Instance ID (required for unmonitor)')
parser.add_option(
  "--format",
  dest="format",
  default="text",
  help='Output format (text|json)')



def printHelpAndExit():
  parser.print_help(sys.stderr)
  sys.exit(1)


def handleListRequest(grok, fmt):
  instances = grok.listInstances()

  if fmt == "json":
    print(json.dumps(instances))
  else:
    table = PrettyTable()

    table.add_column("ID", [x['server'] for x in instances])
    table.add_column("Instance", [x['name'] for x in instances])
    table.add_column("Service", [x['namespace'] for x in instances])
    table.add_column("Region", [x['location'] for x in instances])
    table.add_column("Status", [x['status'] for x in instances])

    table.align = "l"  # left align
    print(table)


def handleUnmonitorRequest(grok, instanceID):
  grok.deleteInstance(instanceID)


def handle(options, args):
  """ `grok instance` handler. """
  try:
    action = args.pop(0)
  except IndexError:
    printHelpAndExit()

  (server, apikey) = grokcli.getCommonArgs(parser, args)

  grok = GrokSession(server=server, apikey=apikey)

  if action == "list":
    handleListRequest(grok, options.format)

  elif action == "unmonitor":
    if not options.id:
      printHelpAndExit()

    handleUnmonitorRequest(grok, options.id)

  else:
    printHelpAndExit()



if __name__ == "__main__":
  handle(*parser.parse_args())
