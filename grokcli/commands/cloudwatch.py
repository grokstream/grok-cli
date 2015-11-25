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



# Subcommand CLI Options

if __name__ == "__main__":
  subCommand = "%prog"
else:
  subCommand = "%%prog %s" % __name__.rpartition('.')[2]

USAGE = """%s (metrics|instances) (list|monitor|unmonitor) \
[GROK_SERVER_URL GROK_API_KEY] [options]

Create Grok cloudwatch model
""".strip() % subCommand



def dimensions_callback(option, opt, value, parser):
  if not hasattr(dimensions_callback, "dimensions"):
    dimensions_callback.dimensions = {}
  dimensions_callback.dimensions[value[0]]=value[1]

parser = OptionParser(usage=USAGE)
parser.add_option(
  "--metric",
  dest="metric",
  metavar="NAME",
  help="Metric name (required for metric monitor, metric unmonitor")
parser.add_option(
  "--instance",
  dest="instance",
  metavar="INSTANCE_ID",
  help="Instance ID (required for monitor, unmonitor)")
parser.add_option(
  "--namespace",
  dest="namespace",
  metavar="NAMESPACE",
  help="Metric namespace (required for monitor, unmonitor)")
parser.add_option(
  "--region",
  dest="region",
  metavar="REGION",
  help="AWS Region (required for monitor, unmonitor)")
parser.add_option(
  "--dimensions",
  dest="dimensions",
  action="callback",
  nargs=2,
  type="str",
  callback=dimensions_callback,
  help="Cloudwatch dimensions (required for metrics monitor)")
parser.add_option(
  "--format",
  dest="format",
  default="text",
  help='Output format (text|json)')

# Implementation

def getCloudwatchMetrics(grok, region=None, namespace=None,
                         instance=None, metricName=None):
  """ Request available metric data for specified region,
      namespace, instance, metric name where provided in CLI context
  """
  # Query Grok regions API for available cloudwatch metrics
  if region:
    regions = [region]
  else:
    regions = grok.listMetrics("cloudwatch")["regions"]

  metrics = []

  for region in regions:
    for metric in grok.listCloudwatchMetrics(region,
                                             namespace=namespace,
                                             instance=instance,
                                             metric=metricName):
      metrics.append(metric)

  return metrics


def handleMetricsMonitorRequest(grok, nativeMetric):
  result = grok.createModel(nativeMetric)
  model = next(iter(result))
  print model["uid"]


def handleMetricsUnmonitorRequest(grok, region, namespace, instance, metric):
  metricName = "{0}/{1}".format(namespace, metric)
  server = "{0}/{1}/{2}".format(region, namespace, instance)

  models = grok.listModels()

  metrics = [m for m in models if (m["datasource"] == "cloudwatch" and
                                   m["name"] == metricName and
                                   m["server"] == server)]

  if not len(metrics):
    raise GrokCLIError("Metric not found")

  grok.deleteModel(metrics[0]["uid"])


def handleInstanceMonitorRequest(grok, region, namespace, instance):
  grok.createInstance(region, namespace, instance)


def handleInstanceUnmonitorRequest(grok, region, namespace, instance):
  instanceID = "{0}/{1}/{2}".format(region, namespace, instance)
  grok.deleteInstance(instanceID)


def tableAddMetricDimensionColumn(table, metrics, column):
  values = []

  for metric in metrics:
    value = ""

    if column in metric['dimensions']:
      c = metric['dimensions'][column]

      if isinstance(c, list): # hack due to weird server response format
        value = c[0]
      else:
        value = c

    values.append(value)

  table.add_column(column, values)


def handleMetricsListRequest(grok, fmt, region=None, namespace=None,
                             metricName=None, instance=None):
  metrics = getCloudwatchMetrics(grok, region=region,
                                 namespace=namespace, instance=instance,
                                 metricName=metricName)

  if fmt == "json":
    print(json.dumps(metrics))
  else:
    table = PrettyTable()

    table.add_column("Region", [x['region'] for x in metrics])
    table.add_column("Namespace", [x['namespace'] for x in metrics])
    table.add_column("Name", [x['name'] if 'name' in x else ''
                     for x in metrics])
    table.add_column("Metric", [x['metric'] for x in metrics])

    tableAddMetricDimensionColumn(table, metrics, 'VolumeId')
    tableAddMetricDimensionColumn(table, metrics, 'InstanceId')
    tableAddMetricDimensionColumn(table, metrics, 'DBInstanceIdentifier')
    tableAddMetricDimensionColumn(table, metrics, 'LoadBalancerName')
    tableAddMetricDimensionColumn(table, metrics, 'AutoScalingGroupName')
    tableAddMetricDimensionColumn(table, metrics, 'AvailabilityZone')

    table.align = "l"  # left align
    print(table)


def handle(options, args):
  """ `grok cloudwatch` handler. """
  try:
    resource = args.pop(0)
    action = args.pop(0)
  except IndexError:
    printHelpAndExit()

  (server, apikey) = grokcli.getCommonArgs(parser, args)

  grok = GrokSession(server=server, apikey=apikey)

  if resource == "metrics":

    if action == "monitor":
      nativeMetric = {
          "datasource": "cloudwatch",
          "metric": options.metric,
          "namespace": options.namespace,
          "region": options.region
        }

      if hasattr(dimensions_callback, "dimensions"):
        nativeMetric["dimensions"] = dimensions_callback.dimensions
      else:
        printHelpAndExit()

      handleMetricsMonitorRequest(grok, nativeMetric)

    elif action == "unmonitor":
      if not (options.region and options.namespace
              and options.instance and options.metric):
        printHelpAndExit()

      handleMetricsUnmonitorRequest(grok, options.region,
                                    options.namespace, options.instance,
                                    options.metric)

    elif action == "list":
      handleMetricsListRequest(
        grok,
        options.format,
        region=options.region,
        namespace=options.namespace,
        metricName=options.metric,
        instance=options.instance)

    else:
      printHelpAndExit()

  elif resource == "instances":

    if action == "monitor":
      if not (options.region and options.namespace and options.instance):
        printHelpAndExit()

      handleInstanceMonitorRequest(grok, options.region,
                                   options.namespace, options.instance)

    elif action == "unmonitor":
      if not (options.region and options.namespace and options.instance):
        printHelpAndExit()

      handleInstanceUnmonitorRequest(grok, options.region,
                                     options.namespace, options.instance)

    elif action == "list":
      print "Not yet implemented"

    else:
      printHelpAndExit()

  else:
    printHelpAndExit()


def printHelpAndExit():
  parser.print_help(sys.stderr)
  sys.exit(1)



if __name__ == "__main__":
  handle(*parser.parse_args())
