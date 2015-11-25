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
from requests.sessions import Session
from requests.models import Request, Response
from requests.exceptions import (
  ConnectionError,
  InvalidURL,
  MissingSchema)
import socket
from urlparse import urlparse
from grokcli.exceptions import (
  GrokCLIError,
  InvalidGrokHostError,
  InvalidCredentialsError)



class GrokCustomContextManager(socket.socket):
  """ Helper class for establishing a socket connection to Grok Custom Metric
      endpoint.  See GrokSession.connect()
  """

  def __init__(self, host, port, *args, **kwargs):
    super(GrokCustomContextManager, self).__init__(*args, **kwargs)
    self._host = host
    self._port = port


  def __enter__(self):
    self.connect((self._host, self._port))
    return self


  def __exit__(self, type, value, traceback):
    self.shutdown(socket.SHUT_WR)
    response = self.recv(4096)
    assert len(response) == 0, "Unexpected TCP response: %s" % response
    self.close()




class GrokSession(Session):
  server = "https://localhost"


  @property
  def apikey(self):
    if self.auth:
      return self.auth[0]


  @apikey.setter
  def apikey(self, value):
    self.auth = (value, None)


  def __init__(self, server=None, apikey=None, *args, **kwargs):
    super(GrokSession, self).__init__(*args, **kwargs)

    if server is not None:
      self.server = server

    if apikey is not None:
      self.apikey = apikey

    self.verify = False


  def _request(self, *args, **kwargs):
    try:
      return self.request(*args, **kwargs)
    except ConnectionError as e:
      if hasattr(e.args[0], "reason"):
        if isinstance(e.args[0].reason, socket.gaierror):
          if e.args[0].reason.args[0] == socket.EAI_NONAME:
            raise InvalidGrokHostError("Invalid hostname")
    except (InvalidURL, MissingSchema) as e:
      raise InvalidGrokHostError("Invalid hostname")


  def connect(self):
    """ Helper function for establishing a socket connection to Grok Custom
        Metric endpoint given a GrokSession instance.  Use as a Context Manager
        to ensure that connection is gracefully shutdown:

          grok = GrokSession(server="...", apikey="...")

          with grok.connect() as sock:
            sock.sendall("{metric name} {metric value} {unix timestamp}\n")
    """
    parseResult = urlparse(self.server)
    return GrokCustomContextManager(parseResult.netloc, 2003)


  def verifyCredentials(self, aws_access_key_id, aws_secret_access_key, **kwargs):
    data = {
      "aws_access_key_id": aws_access_key_id,
      "aws_secret_access_key": aws_secret_access_key,
    }

    response = self._request(
      method="POST",
      url=self.server + "/_auth",
      data=json.dumps(data),
      allow_redirects=False,
      **kwargs)

    if response.status_code == 200:
      result = json.loads(response.text)
      if result["result"] == "success":
        return result["apikey"]
    elif 300 <= response.status_code < 400:
      raise InvalidGrokHostError("Invalid protocol")

    raiseError(InvalidCredentialsError,
               "Unable to verify credentials.",
               response)


  def updateSettings(self, settings, section=None, **kwargs):

    url = self.server + "/_settings"

    if section is not None:
      url += "/" + section

    response = self._request(
      method="POST",
      url=url,
      data=json.dumps(settings),
      auth=self.auth,
      **kwargs)

    if response.status_code == 204:
      return

    raiseError(GrokCLIError, "Unable to update settings.", response)


  def listMetricDatasources(self, **kwargs):

    response = self._request(
      method="GET",
      url=self.server + "/_metrics",
      auth=self.auth,
      **kwargs)

    if response.status_code == 200:
      return json.loads(response.text)

    raiseError(GrokCLIError, "Unable to list metric datasources.", response)


  def listMetrics(self, datasource, **kwargs):

    response = self._request(
      method="GET",
      url=self.server + "/_metrics/" + datasource,
      auth=self.auth,
      **kwargs)

    if response.status_code == 200:
      return json.loads(response.text)

    raiseError(GrokCLIError, "Unable to list metrics.", response)


  def listCloudwatchMetrics(self, region, namespace=None, instance=None,
    metric=None, **kwargs):

    url = self.server + "/_metrics/cloudwatch/"
    if namespace:
      url += region + "/" + namespace
      if metric:
        url += "/" + metric
      elif instance:
        url += "/instances/" + instance
    else:
      url += "regions/" + region

    response = self._request(
      method="GET",
      url=url,
      auth=self.auth,
      **kwargs)

    if response.status_code == 200:
      return json.loads(response.text)

    raiseError(GrokCLIError, "Unable to list metrics.", response)


  def listAutostackMetrics(self, stackID, **kwargs):

    response = self._request(
      method="GET",
      url=self.server + "/_autostacks/" + stackID + "/metrics",
      auth=self.auth,
      **kwargs)

    if response.status_code == 200:
      return json.loads(response.text)

    raiseError(GrokCLIError, "Unable to list metrics.", response)


  def listModels(self, **kwargs):

    response = self._request(
      method="GET",
      url=self.server + "/_models",
      auth=self.auth,
      **kwargs)

    if response.status_code == 200:
      return json.loads(response.text)

    raiseError(GrokCLIError, "Unable to list models.", response)


  def listInstances(self, **kwargs):

    response = self._request(
      method="GET",
      url=self.server + "/_instances",
      auth=self.auth,
      **kwargs)

    if response.status_code == 200:
      return json.loads(response.text)

    raiseError(GrokCLIError, "Unable to list instances.", response)


  def listAutostackInstances(self, stackID, **kwargs):

    response = self._request(
      method="GET",
      url=self.server + "/_autostacks/" + stackID + "/instances",
      auth=self.auth,
      **kwargs)

    if response.status_code == 200:
      return json.loads(response.text)

    raiseError(GrokCLIError, "Unable to list instances.", response)


  def listAutostacks(self, **kwargs):

    response = self._request(
      method="GET",
      url=self.server + "/_autostacks",
      auth=self.auth,
      **kwargs)

    if response.status_code == 200:
      return json.loads(response.text)

    raiseError(GrokCLIError, "Unable to list autostacks.", response)


  def exportModels(self, **kwargs):

    response = self._request(
      method="GET",
      url=self.server + "/_models/export",
      auth=self.auth,
      **kwargs)

    if response.status_code == 200:
      return json.loads(response.text)

    raiseError(GrokCLIError, "Unable to export models.", response)


  def exportModel(self, modelId, **kwargs):

    response = self._request(
      method="GET",
      url=self.server + "/_models/" + modelId + "/export",
      auth=self.auth,
      **kwargs)

    if response.status_code == 200:
      return json.loads(response.text)

    raiseError(GrokCLIError, "Unable to export model.", response)


  def createModels(self, nativeMetric, **kwargs):

    url = self.server + "/_models"

    response = self._request(
      method="POST",
      url=url,
      data=json.dumps(nativeMetric),
      auth=self.auth,
      **kwargs)

    if response.status_code == 201:
      return json.loads(response.text)

    raiseError(GrokCLIError, "Unable to create models.", response)


  def createModel(self, nativeMetric, **kwargs):
    url = self.server + "/_models"

    response = self._request(
      method="POST",
      url=url,
      data=json.dumps(nativeMetric),
      auth=self.auth,
      **kwargs)

    if response.status_code == 201:
      return json.loads(response.text)

    raiseError(GrokCLIError, "Unable to create model.", response)


  def createInstance(self, region, namespace, instanceID, **kwargs):
    url = (self.server + "/_instances/" +
          region + "/" + namespace + "/" + instanceID)

    response = self._request(
      method="POST",
      url=url,
      auth=self.auth,
      **kwargs)

    if response.status_code == 200:
      return json.loads(response.text)

    raiseError(GrokCLIError, "Unable to create instance.", response)


  def previewAutostack(self, region, filters, **kwargs):
    params = "?region={0}&filters={1}".format(region, json.dumps(filters))
    url = self.server + "/_autostacks/preview_instances" + params

    response = self._request(
      method="GET",
      url=url,
      auth=self.auth,
      **kwargs)

    if response.status_code == 200:
      return json.loads(response.text)

    raiseError(GrokCLIError, "Unable to preview autostack.", response)


  def createAutostack(self, name, region, filters, **kwargs):
    url = self.server + "/_autostacks"
    stack = {
      "name": name,
      "region": region,
      "filters": filters
    }

    response = self._request(
      method="POST",
      url=url,
      data=json.dumps(stack),
      auth=self.auth,
      **kwargs)

    if response.status_code == 201:
      return json.loads(response.text)

    raiseError(GrokCLIError, "Unable to create autostack.", response)


  def addMetricToAutostack(self, stackID, metricNamespace, metricName, **kwargs):
    url = self.server + "/_autostacks/" + stackID + "/metrics"
    data = json.dumps([{ "namespace": metricNamespace, "metric": metricName }])

    response = self._request(
      method="POST",
      url=url,
      data=data,
      auth=self.auth,
      **kwargs)

    if response.status_code == 201:
      return

    raiseError(GrokCLIError, "Unable to add metric to autostack.", response)


  def deleteModel(self, metricID, **kwargs):
    url = self.server + "/_models/" + metricID

    response = self._request(
      method="DELETE",
      url=url,
      auth=self.auth,
      **kwargs)

    if response.status_code == 200:
      return json.loads(response.text)

    raiseError(GrokCLIError, "Unable to delete model.", response)


  def deleteInstance(self, serverName, **kwargs):
    url = self.server + "/_instances"

    response = self._request(
      method="DELETE",
      url=url,
      data=json.dumps([serverName]),
      auth=self.auth,
      **kwargs)

    if response.status_code == 200:
      return json.loads(response.text)

    raiseError(GrokCLIError, "Unable to delete instance.", response)


  def deleteAutostack(self, stackID, **kwargs):
    url = self.server + "/_autostacks/" + stackID

    response = self._request(
      method="DELETE",
      url=url,
      auth=self.auth,
      **kwargs)

    if response.status_code == 204:
      return

    raiseError(GrokCLIError, "Unable to delete autostack.", response)


  def removeMetricFromAutostack(self, stackID, metricID, **kwargs):
    url = self.server + "/_autostacks/" + stackID + "/metrics/" + metricID

    response = self._request(
      method="DELETE",
      url=url,
      auth=self.auth,
      **kwargs)

    if response.status_code == 204:
      return

    raiseError(GrokCLIError, "Unable to remove metric from autostack.",
               response)



def raiseError(error, message, response):
  raise error("{0}\nMessage: {1}".format(message, response.text))



__all__ = [
  "GrokCLIError",
  "GrokSession",
  "InvalidGrokHostError",
  "InvalidCredentialsError"]
