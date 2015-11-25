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
import os
try:
  import yaml
except ImportError:
  pass
import sys
from functools import partial
from optparse import OptionParser

import commands
from exceptions import GrokCLIError
import __version__


availableCommands = __import__("grokcli.commands", globals(), locals(), ['*'])

commands = dict([
    (cmd, getattr(availableCommands, cmd))
    for cmd in availableCommands.__all__
  ])

usage = "%prog [command] [options]\n\n" \
        "Available commands:\n"

for command in sorted(commands):
  usage += "\n    " + command

parser = OptionParser(usage=usage, version=__version__.__version__)


def handle(options, args):
  parser.print_help()


def main():
  try:
    subcommand = sys.argv.pop(1)
  except IndexError:
    parser.print_help(sys.stderr)
    sys.exit()

  if subcommand == "--version":
    print(__version__.__version__)
    sys.exit()

  submodule = commands.get(subcommand, sys.modules[__name__])

  (options, args) = submodule.parser.parse_args(sys.argv[1:])

  try:
    submodule.handle(options, args)
  except GrokCLIError as e:
    print >> sys.stderr, "ERROR:", e.message
    sys.exit(1)


# Use yaml by default, if it's available
if "yaml" in sys.modules:
  load = yaml.safe_load
  dump = partial(yaml.safe_dump, default_flow_style=False)
else:
  load = json.loads
  dump = partial(json.dumps, indent=2)


def getCommonArgs(parser, args):
  env = os.environ
  if ('GROK_SERVER_URL' in env) and ('GROK_API_KEY' in env):
    return (env['GROK_SERVER_URL'], env['GROK_API_KEY'])

  try:
    server = args.pop(0)
    apikey = args.pop(0)
  except IndexError:
    parser.print_help(sys.stderr)
    sys.exit(1)

  return (server, apikey)
