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
from grokcli.exceptions import GrokCLIError


if __name__ == "__main__":
  subCommand = "%prog"
else:
  subCommand = "%%prog %s" % __name__.rpartition('.')[2]

USAGE = """%s (stacks|metrics|instances) (list|create|delete|add|remove) \
[GROK_SERVER_URL GROK_API_KEY] [options]

Browse...
""".strip() % subCommand


parser = OptionParser(usage=USAGE)
parser.add_option(
  "--id",
  dest="id",
  help=('Stack ID (required for '
    'delete, add, remove, metrics list, instances list [or provide --name])'))
parser.add_option(
  "--name",
  dest="name",
  help=('Stack name (required for create; delete, '
    'add, remove, metrics list, instances list [or provide --id])'))
parser.add_option(
  "--region",
  dest="region",
  help=('AWS region (required for create, delete, add, remove, '
                    'metrics list, instances list)'))
parser.add_option(
  "--filters",
  dest="filters",
  help='Filters (required for create)')
parser.add_option(
  "--preview",
  dest="preview",
  action="store_true",
  default=False,
  help='Preview (use with create)')
parser.add_option(
  "--metric_id",
  dest="metricID",
  help='Metric ID (required for metrics remove)')
parser.add_option(
  "--metric_namespace",
  dest="metricNamespace",
  help='Metric Namespace (required for metrics add)')
parser.add_option(
  "--metric_name",
  dest="metricName",
  help='Metric Name (required for metrics add)')
parser.add_option(
  "--format",
  dest="format",
  default="text",
  help='Output format (text|json)')



def printHelpAndExit():
  parser.print_help(sys.stderr)
  sys.exit(1)


def findStackByName(grok, name, region):
  stacks = grok.listAutostacks()
  foundStacks = [s for s in stacks if
                 (s['name'] == name and s['region'] == region)]

  if not len(foundStacks):
    raise GrokCLIError("Autostack not found")

  return foundStacks[0]['uid']


def handleListRequest(grok, fmt):
  stacks = grok.listAutostacks()

  if fmt == "json":
    print(json.dumps(stacks))
  else:
    table = PrettyTable()

    table.add_column("ID", [x['uid'] for x in stacks])
    table.add_column("Name", [x['name'] for x in stacks])
    table.add_column("Region", [x['region'] for x in stacks])
    table.add_column("Filters", [x['filters'] for x in stacks])

    table.align = "l"  # left align
    print(table)


def handlePreviewRequest(grok, fmt, region, filters):
  instances = grok.previewAutostack(region, filters)

  if fmt == "json":
    print(json.dumps(instances))
  else:
    table = PrettyTable()

    table.add_column("ID", [x['instanceID'] for x in instances])
    table.add_column("Instance",
                     [x['tags']['Name'] if 'Name' in x['tags'] else ''
                     for x in instances])
    table.add_column("Region", [x['regionName'] for x in instances])
    table.add_column("State", [x['state'] for x in instances])

    table.align = "l"  # left align
    print(table)


def handleCreateRequest(grok, name, region, filters):
  grok.createAutostack(name, region, filters)


def handleDeleteRequest(grok, stackID, stackName, region):
  if not stackID:
    stackID = findStackByName(grok, stackName, region)

  grok.deleteAutostack(stackID)


def handleMetricsListRequest(grok, stackID, stackName, region, fmt):
  if not stackID:
    stackID = findStackByName(grok, stackName, region)

  metrics = grok.listAutostackMetrics(stackID)

  if fmt == "json":
    print(json.dumps(metrics))
  else:
    table = PrettyTable()

    table.add_column("ID", [x['uid'] for x in metrics])
    table.add_column("Display Name", [x['display_name'] for x in metrics])
    table.add_column("Name", [x['name'] for x in metrics])
    table.add_column("Status", [x['status'] for x in metrics])

    table.align = "l"  # left align
    print(table)


def handleMetricsAddRequest(grok, stackID, stackName, region,
                            metricNamespace, metricName):
  if not stackID:
    stackID = findStackByName(grok, stackName, region)

  grok.addMetricToAutostack(stackID, metricNamespace, metricName)


def handleMetricsRemoveRequest(grok, stackID, stackName, region, metricID):
  if not stackID:
    stackID = findStackByName(grok, stackName, region)

  grok.removeMetricFromAutostack(stackID, metricID)


def handleInstancesListRequest(grok, stackID, stackName, region, fmt):
  if not stackID:
    stackID = findStackByName(grok, stackName, region)

  instances = grok.listAutostackInstances(stackID)

  if fmt == "json":
    print(json.dumps(instances))
  else:
    table = PrettyTable()

    table.add_column("Instance", [x['instanceID'] for x in instances])
    table.add_column("Type", [x['instanceType'] for x in instances])
    table.add_column("Region", [x['regionName'] for x in instances])
    table.add_column("State", [x['state'] for x in instances])

    table.align = "l"  # left align
    print(table)


def handle(options, args):
  """ `grok autostacks` handler. """
  try:
    resource = args.pop(0)
    action = args.pop(0)
  except IndexError:
    printHelpAndExit()

  (server, apikey) = grokcli.getCommonArgs(parser, args)

  grok = GrokSession(server=server, apikey=apikey)

  if resource == "stacks":

    if action == "list":
      handleListRequest(grok, options.format)

    elif action == "create":
      if not (options.region and options.filters):
        printHelpAndExit()

      filters = json.loads(options.filters)

      if options.preview:
        handlePreviewRequest(grok, options.format,
                             options.region, filters)
      else:
        if not options.name:
          printHelpAndExit()

        handleCreateRequest(grok,
                            options.name, options.region, filters)

    elif action == "delete":
      if not (options.id or (options.name and options.region)):
        printHelpAndExit()

      handleDeleteRequest(grok, options.id, options.name, options.region)

    else:
      printHelpAndExit()

  elif resource == "metrics":

    if not (options.id or (options.name and options.region)):
      printHelpAndExit()

    if action == "list":
      handleMetricsListRequest(grok,
                               options.id,
                               options.name,
                               options.region,
                               options.format)

    elif action == "add":
      if not (options.metricNamespace and options.metricName):
        printHelpAndExit()

      handleMetricsAddRequest(grok,
                              options.id,
                              options.name,
                              options.region,
                              options.metricNamespace,
                              options.metricName)

    elif action == "remove":
      if not options.metricID:
        printHelpAndExit()

      handleMetricsRemoveRequest(grok,
                                 options.id,
                                 options.name,
                                 options.region,
                                 options.metricID)

  elif resource == "instances":

    if not (options.id or (options.name and options.region)):
      printHelpAndExit()

    if action == "list":
      handleInstancesListRequest(grok,
                                 options.id,
                                 options.name,
                                 options.region,
                                 options.format)

  else:
    printHelpAndExit()



if __name__ == "__main__":
  handle(*parser.parse_args())
