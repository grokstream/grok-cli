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
import sys
from functools import partial
from optparse import OptionParser
from grokcli.api import GrokSession
import grokcli

# Subcommand CLI Options

if __name__ == "__main__":
  subCommand = "%prog"
else:
  subCommand = "%%prog %s" % __name__.rpartition('.')[2]

USAGE = """%s [GROK_SERVER_URL GROK_API_KEY]

Export Grok model definitions.
""".strip() % subCommand

parser = OptionParser(usage=USAGE)
parser.add_option(
  "-o",
  "--output",
  dest="output",
  metavar="FILE",
  help="Write output to FILE instead of stdout")
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
  """ `grok export` handler. """
  (server, apikey) = grokcli.getCommonArgs(parser, args)

  dump = partial(json.dumps, indent=2)

  if hasattr(options, "useYaml"):
    if options.useYaml:
      dump = partial(yaml.safe_dump, default_flow_style=False)

  grok = GrokSession(server=server, apikey=apikey)

  if options.output is not None:
    outp = open(options.output, "w")
  else:
    outp = sys.stdout

  models = grok.exportModels()

  if models:
    try:
      print >> outp, dump(models)
    finally:
      outp.flush()
      if outp != sys.stdout:
        outp.close()


if __name__ == "__main__":
  handle(*parser.parse_args())
