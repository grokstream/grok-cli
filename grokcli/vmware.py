import optparse
import requests
import sys
import os
import time
from time import sleep

from grokcli.api import GrokSession
from pysphere import VIServer

def getMaxValue(group):
  return {
        'net': 10000000,
        'cpu': 100,
        'mem': 100,
        'disk': 1000000,
  }.get(group, None)

def getVMdata(configFilePath, host, user, password, vmListFile):
  if (host is None and user is None and password is None):
    OPTION_CHAR = '='
    options = {}
    if os.path.exists(configFilePath):
      content = open(configFilePath)
      for line in content:
        if OPTION_CHAR in line:
          option, value = line.split(OPTION_CHAR, 1)
          option = option.strip()
          value = value.strip()

          if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
            options[option] = value

      HOST = options['HOST']
      USER = options['USER']
      PASSWORD = options['PASSWORD']
    else:
      print "Must supply valid ESX configuration file."
      sys.exit(1)
  else:
    HOST = host
    USER = user
    PASSWORD = password

  try:
    server = VIServer()
    server.connect(HOST, USER, PASSWORD)

    if vmListFile is None:
      vmlist = server.get_registered_vms()
    else:
      if os.path.exists(vmListFile):
        fileptr = open(vmListFile)
        content = fileptr.read()
        vmlist = content.split(",")

    metric = []

    vmMetrics = {'disk.write': 131079, 'disk.read': 131078, 'disk.usage': 131073, 'cpu.usage': 1,'mem.usage': 65537}
    for vms in vmlist:
      vms = vms.strip()
      start = vms.find(']') + 2
      end = vms.find('/', start)
      vmName = vms[start:end]
      pm = server.get_performance_manager()
      vm = server.get_vm_by_path(vms)
      mor = vm._mor
      for key, value in vmMetrics.iteritems():
        entitystats = pm.get_entity_statistic(mor, key)
        for i in entitystats:
          dict_result = dict((name, getattr(i, name)) for name in dir(i))
          metric_name = vmName+'.'+dict_result['group']+'.'+dict_result['counter']
          group = dict_result['group']
          timeTuple = dict_result['time']
          ts = time.mktime(timeTuple.timetuple())
          maxValue = getMaxValue(group)
          if dict_result['unit'] == 'percent':
            mvalue = float(dict_result['value'])/100
          else:
            mvalue = dict_result['value']
          metric.append({"metric_name": metric_name, "value": mvalue, "unit":dict_result['unit'], "server":vmName, "maxValue":maxValue,"time_stamp":ts})

    return metric
  except Exception as e:
    print e
    sys.exit(1)


def sendVMDataToGrok(grokServer, grokApiKey, configFilePath, host, user, password, vmListFile):
  grok = GrokSession(server=grokServer, apikey=grokApiKey)
  metric = getVMdata(configFilePath, host, user, password, vmListFile)

  if metric is not None:
    try:
      response = grok.post(grok.server + "/_vmware/", json=metric, auth=grok.auth)
      print response.text
      sleep(10)
      if response.status_code == 200:
        print "Data sent to Grok."
        sys.exit(1)
      else:
        print "Error sending data to Grok."
        sys.exit(1)
    except requests.exceptions.ConnectionError as e:
      print e
      sys.exit(1)
    except Exception as e:
      print e
      sys.exit(1)
  else:
    print "Error connecting to ESX server."
    sys.exit(1)


if __name__ == "__main__":
  usage = "usage: %prog [options]"
  parser = optparse.OptionParser(usage=usage)
  parser.add_option("--grokServer", help="the Grok server URL")
  parser.add_option("--grokApiKey", help="the Grok server API key")
  parser.add_option("--configFilePath", help="the ESX config file")
  parser.add_option("--host", help="the ESX host to connect to")
  parser.add_option("--user", help="the ESX Username to use when connecting to host")
  parser.add_option("--password", help="the ESX password to use when connecting to host")
  parser.add_option("--vmFileList", help="the VMs to collect data from")

  (options, args) = parser.parse_args()

  if options.grokServer is None:
    print "Must supply valid grokServer."
    sys.exit(1)

  if options.grokApiKey is None:
    print "Must supply valid grokApiKey."
    sys.exit(1)

  if options.configFilePath is None or (options.host is None and options.user is None and options.password is None):
    print "Must supply valid ESX configuration."
    sys.exit(1)

  sendVMDataToGrok(options.grokServer, options.grokApiKey, options.configFilePath, options.host, options.user, options.password, options.vmFileList)