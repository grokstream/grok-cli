#!/bin/bash
#------------------------------------------------------------------------------
# Copyright 2014 Numenta Inc.
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

OPTIND=1

AWS_REGION=""
GROK_SERVER=""
INSTANCES_TO_MONITOR=""

show_credential_usage() {
  echo "You must set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
  echo " before running this example."
  echo
  echo "ex: AWS_SECRET_ACCESS_KEY='foo' AWS_ACCESS_KEY_ID='bar' ./$0"
  echo
  echo "or"
  echo
  echo "export AWS_ACCESS_KEY_ID=YOURACCESSKEY"
  echo "export AWS_SECRET_ACCESS_KEY=YOURSECRETKEY"
  echo "./$0"
  echo
}

show_help() {
  show_credential_usage
  echo "$0 -s https://your.grok.server -r AWS_REGION -g serverType"
  echo
  echo "If you are working with a running server, add -a API_KEY"
  echo
  echo "This example script assumes you have instances with a server:type tag,"
  echo "an environment tag, and that there are nodes with environment set"
  echo "to production."
  echo
}

parse_cli(){
  while getopts "ha:g:r:s:" opt; do
    case "$opt" in
      h) show_help
         exit 0
         ;;
      a) GROK_API_KEY="$OPTARG"
         ;;
      g) AUTO_SCALE_GROUP_ID="$AUTO_SCALE_GROUP_ID $OPTARG"
         ;;
      r) AWS_REGION="$OPTARG"
         ;;
      s) GROK_SERVER="$OPTARG"
         ;;
    esac
  done
}

sanity_check_configuration() {
  if [ -z $AWS_ACCESS_KEY_ID ]; then
    show_credential_usage
    exit 1
  fi
  if [ -z $AWS_SECRET_ACCESS_KEY ]; then
    show_credential_usage
    exit 1
  fi
  if [ "$AWS_REGION" == "" ]; then
    echo "You must specify the AWS region with -r"
    show_help
    exit 1
  fi
  if [ "$GROK_SERVER" == "" ]; then
    echo "You must specify the Grok server to configure with -s"
    show_help
    exit 1
  fi
  which grok &> /dev/null
  if [ $? != 0 ]; then
    echo 'grok needs to be installed and in your $PATH'
    echo
    echo "Have you run python setup.py install or pip install grokcli yet?"
    exit 1
  fi
}

set_server_credentials() {
  grok credentials ${GROK_SERVER} \
    --AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
    --AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
    --accept-eula
}

add_example_autostack() {
  echo "Adding autostacks..."
  for autostack in ${AUTO_SCALE_GROUP_ID}
  do
    echo "Creating autostack ${autostack}..."
    # First, create the autostack
    printf -v aws_filter '{"tag:server:type":["%s"], "tag:environment":["production"]}' ${autostack}
    grok autostacks stacks create ${GROK_SERVER} ${GROK_API_KEY} \
       --name="${autostack}" \
       --region="${AWS_REGION}" \
       --filters=$aws_filter
    # List the instances in the autostack
    echo "Found the following instances for ${autostack}"
    grok autostacks instances list ${GROK_SERVER} ${GROK_API_KEY} \
       --name="${autostack}" \
       --region="${AWS_REGION}"

    # Add a default set of metrics like the Web UI does
    # Network
    echo "Adding NetworkIn metric"
    grok autostacks metrics add ${GROK_SERVER} ${GROK_API_KEY} \
      --name="${autostack}" \
      --region="${AWS_REGION}" \
      --name="${autostack}" \
      --metric_namespace='AWS/EC2' --metric_name=NetworkIn

    # Disk writes
    echo "Adding DiskWriteBytes metric"
    grok autostacks metrics add ${GROK_SERVER} ${GROK_API_KEY} \
      --name="${autostack}" \
      --region="${AWS_REGION}" \
      --name="${autostack}" \
      --metric_namespace='AWS/EC2' --metric_name=DiskWriteBytes

    # And CPU
    echo "Adding CPUUtilization metric"
    grok autostacks metrics add ${GROK_SERVER} ${GROK_API_KEY} \
      --name="${autostack}" \
      --region="${AWS_REGION}" \
      --name="${autostack}" \
      --metric_namespace='AWS/EC2' --metric_name=CPUUtilization
  done
}

configure_grok_server() {
  if [ -z ${GROK_API_KEY} ]; then
    echo "Setting server credentials"
    GROK_API_KEY=$(set_server_credentials)
    echo "Generated GROK_API_KEY, ${GROK_API_KEY}"
  else
    echo "Using preset GROK_API_KEY: ${GROK_API_KEY}"
  fi
  if [ ! -z $AUTO_SCALE_GROUP_ID ]; then
    add_example_autostack
  fi
}

parse_cli $*
sanity_check_configuration

echo "Configuring ${GROK_SERVER}..."
configure_grok_server
echo

echo "Autostacks monitored: "
grok autostacks stacks list ${GROK_SERVER} ${GROK_API_KEY} --region=${AWS_REGION}
echo
