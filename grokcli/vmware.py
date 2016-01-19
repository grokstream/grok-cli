import optparse
import sys
import os

from grokcli.api import GrokSession
from pysphere import VIServer

def getMaxValue(group):
  return {
        'net': 10000000,
        'cpu': 100,
        'mem': 100,
        'disk': 1000000,
  }.get(group, None)

def getVMdata(configFilePath):

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

    try:
      server = VIServer()
      #connecting to the vsphere
      server.connect(HOST, USER, PASSWORD, trace_file="vmwaredebug.txt")

      #getting installed vms on vmware
      vmlist = server.get_registered_vms()

      #Selected few metrics from vmware
      vmMetrics = {'disk.write': 131079, 'disk.read': 131078, 'disk.usage': 131073, 'cpu.usage': 1,'mem.usage': 65537}

      metric = []
      for vms in vmlist:
        #Get installed vms on hypervisor
        #Fetch the server name(i.e CentOS_7)  from the path (i.e [datastore1] CentOS_7/CentOS_7.vmx)
        start = vms.find(']') + 2
        end = vms.find('/', start)
        vmName = vms[start:end]
        pm = server.get_performance_manager()
        vm = server.get_vm_by_path(vms)
        #managed object reference for the VM
        mor = vm._mor
        # #returns the metric name and metric ids
        # counterValues = pm.get_entity_counters(mor)
        for key, value in vmMetrics.iteritems():
          entitystats = pm.get_entity_statistic(mor, key)
          for i in entitystats:
            dict_result = dict((name, getattr(i, name)) for name in dir(i))
            metric_name = vmName+'.'+dict_result['group']+'.'+dict_result['counter']
            group = dict_result['group']
            maxValue = getMaxValue(group)
            if dict_result['unit'] == 'percent':
              mvalue = float(dict_result['value'])/100
            else:
              mvalue = dict_result['value']
            metric.append({"metric_name": metric_name, "value": mvalue, "unit":dict_result['unit'], "server":vmName, "maxValue":maxValue})

      return metric
    except Exception as e:
      print e
  else:
    print "Incorrect file path"
    sys.exit(1)

def sendVMDataToGrok(grokServer, grokApiKey, configFilePath):

  grok = GrokSession(server=grokServer, apikey=grokApiKey)

  metric = getVMdata(configFilePath)

  if metric is not None:
    response = grok.post(grok.server + "/_vmware/",json=metric, auth=grok.auth)
    print response
    print response.text
    if response.status_code == 200:
      print "Data has been sent to grok"
    else:
      print "Error in sending Data"
  else:
    print "Error in connecting to ESX Server."
    sys.exit(1)


if __name__ == "__main__":
  usage = "usage: %prog [options]"
  parser = optparse.OptionParser(usage=usage)
  parser.add_option("--grokServer", help="the Grok server URL")
  parser.add_option("--grokApiKey", help="the Grok server API key")
  parser.add_option("--configFilePath", help="the ESX config file")

  (options, args) = parser.parse_args()

  if options.grokServer is None:
    print "Must supply valid grokServer"
    sys.exit(1)

  if options.grokApiKey is None:
    print "Must supply valid grokApiKey"
    sys.exit(1)

  if options.configFilePath is None:
    print "Must supply ESX config file. Provide full path of the config file."
    sys.exit(1)

  sendVMDataToGrok(options.grokServer, options.grokApiKey, options.configFilePath)