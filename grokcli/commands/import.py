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
try:
  import yaml
except ImportError:
  import json # yaml not available, fall back to json
import select
import sys

from functools import partial
from grokcli.api import GrokSession
import grokcli
from optparse import OptionParser

# Subcommand CLI Options

if __name__ == "__main__":
  subCommand = "%prog"
else:
  subCommand = "%%prog %s" % __name__.rpartition('.')[2]

USAGE = """%s [GROK_SERVER_URL GROK_API_KEY] [FILE]

Import Grok model definitions.
""".strip() % subCommand

parser = OptionParser(usage=USAGE)
parser.add_option(
  "-d",
  "--data",
  dest="data",
  metavar="FILE or -",
  help="Path to file containing Grok model definitions, or - if you " \
       "want to read the data from stdin.")

# Implementation

def importMetricsFromFile(grok, fp, **kwargs):
  models = grokcli.load(fp.read())
  result = grok.createModels(models)


def handle(options, args):
  """ `grok import` handler. """
  (server, apikey) = grokcli.getCommonArgs(parser, args)

  if options.data:
    data = options.data
  else:
    # Pop data source off args
    try:
      data = args.pop(0)
    except IndexError:
      data = "-"

  grok = GrokSession(server=server, apikey=apikey)

  if data.strip() == "-":
    if select.select([sys.stdin,],[],[],0.0)[0]:
      importMetricsFromFile(grok, sys.stdin, **vars(options))
    else:
      parser.print_help()
      sys.exit(1)
  elif data:
    with open(data, "r") as fp:
      importMetricsFromFile(grok, fp, **vars(options))




if __name__ == "__main__":
  handle(*parser.parse_args())
