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

"""Pull data from Grok and upload to Datadog.

This script takes the metric ID for a Grok metric and downloads the most recent
data. It is designed to be run every five minutes or so and will upload
duplicate records. This is fine as long as you don't select "sum" for the
aggregation method in Datadog.

The data is uploaded as two separate Datadog metrics. One for the values and one
for the anomaly scores. The Grok metric server is used as the Datadog host. The
Grok metric name is combined with either ".value" or ".anomalyScore" to make up
the Datadog metric name.

Anomaly scores are transformed from what the Grok API returns into what is
shown in the Grok mobile client as the height of the bars.

Note: This sample requires the `datadog` python library, which can be installed with
the samples bundle: `pip install grokcli[samples]`.
"""

import calendar
import datetime
import math
import optparse
import sys
import ast
import json

from datadog import initialize, api

from grokcli.api import GrokSession


def _getMetricServerAndName(grok, metricId):
  """Gets the server and metric names for the metric with the given ID.

  :param grok: the GrokSession instance
  :param metricId: the Grok metric ID for the desired metric
  :return: the server name and metric name for the Grok metric
  """
  response = grok.get(grok.server + "/_models/" + metricId,
                      auth=grok.auth)

  model = json.loads(response.text)
  return model[0]['server'], model[0]['name']



def _tranformAnomalyScore(score):
  """Transform anomaly score to match Grok mobile bar height.

  :param score: the "anomaly_score" value returned by the Grok API
  :return: the value corresponding to the height of the anomaly bars in Grok
      mobile
  """
  if score > 0.99999:
    return 1.0

  return math.log(1.0000000001 - score) / math.log(1.0 - 0.9999999999)



def _getMetricData(grok, metricId, numRecords):
  """Get metric data from the Grok API and convert to the Datadog format.

  This includes a data transformation for the anomaly score to a value that
  matches the height of the bars in the mobile client.

  :param grok: the GrokSession instance
  :param metricId: the ID of the metric to get data for
  :param numRecords: the number of records to get from the API
  :return: a 2-tuple of values and anomalies lists where each element in the
      lists is a 2-tuple containing the unix timestamp and the value
  """
  url = grok.server + "/_models/" + metricId + "/data"
  if numRecords:
    url += "?limit=%i" % numRecords
  response = grok.get(url, auth=grok.auth)
  data = response.text
  data = ast.literal_eval(data)
  data = data['data']
  valuesData = []
  anomaliesData = []
  first = None
  last = None
  for dtStr, value, anomalyScore, _ in reversed(data):
    if not first:
      first = dtStr
    last = dtStr
    dt = datetime.datetime.strptime(dtStr, "%Y-%m-%d %H:%M:%S")
    ts = calendar.timegm(dt.utctimetuple())
    valuesData.append((ts, value))
    transformedAnomalyScore = _tranformAnomalyScore(anomalyScore)
    anomaliesData.append((ts, transformedAnomalyScore))
  print "First: %s and last: %s" % (first, last)
  return valuesData, anomaliesData



def sendDataToDatadog(datadogApiKey, grokServer, grokApiKey, numRecords,
                      metricId):
  """Get data from Grok and send to Datadog.

  This gets metric data for the metric matching metricId and converts it into
  two datasets in the Datadog format: one for the values and one for the
  anomaly scores.
  """

  # Configure the Datadog python library
  options = {
    'api_key': datadogApiKey
  }

  initialize(**options)

  grok = GrokSession(server=grokServer, apikey=grokApiKey)
  server, metricName = _getMetricServerAndName(grok, metricId)
  valuesData, anomaliesData = _getMetricData(grok, metricId, numRecords)

  # Hack to limit number of records for Grok instances prior to version 1.3
  # that don't respect the limit parameter when getting metric data.
  valuesData = valuesData[-numRecords:]
  anomaliesData = anomaliesData[-numRecords:]

  print "Sending %i records for metric %s on server %s" % (
      len(valuesData), metricName, server)
  response = api.Metric.send(metric=metricName + ".value", points=valuesData, host=server)

  if response["status"] != "ok":
    print "Datadog upload failed with response:\n\n%r" % response

  response = api.Metric.send(metric=metricName + ".anomalyScore", points=anomaliesData, host=server)

  if response["status"] != "ok":
    print "Datadog upload failed with response:\n\n%r" % response



if __name__ == "__main__":
  usage = "usage: %prog [options] metricId"
  parser = optparse.OptionParser(usage=usage)
  parser.add_option("--datadogApiKey", help="the API key for Datadog")
  parser.add_option("--grokServer", help="the Grok server URL")
  parser.add_option("--grokApiKey", help="the Grok server API key")
  parser.add_option("--numRecords", type="int", default=6,
                    help="the number of records to fetch, or 0 to get all")

  options, extraArgs = parser.parse_args()

  if len(extraArgs) != 1:
    parser.error("incorrect number of arguments, expected 1 but got %i" %
                 len(extraArgs))

  if options.datadogApiKey is None:
    print "Must supply valid datadogApiKey"
    sys.exit(1)

  if options.grokServer is None:
    print "Must supply valid grokServer"
    sys.exit(1)

  if options.grokApiKey is None:
    print "Must supply valid grokApiKey"
    sys.exit(1)

  if options.numRecords is None:
    print "Must supply valid numRecords"
    sys.exit(1)

  sendDataToDatadog(options.datadogApiKey, options.grokServer, options.grokApiKey, options.numRecords, extraArgs[0])
