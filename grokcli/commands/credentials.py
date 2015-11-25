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
import socket
import sys

from optparse import OptionParser
from grokcli.api import GrokSession
from grokcli.exceptions import GrokCLIError


# Subcommand CLI Options

if __name__ == "__main__":
  subCommand = "%prog"
else:
  subCommand = "%%prog %s" % __name__.rpartition('.')[2]

USAGE = """%s GROK_SERVER_URL [OPTIONS]

Add AWS credentials to a Grok server configuration.
""".strip() % subCommand

parser = OptionParser(usage=USAGE)

parser.add_option(
  "--accept-eula",
  dest="acceptEULA",
  action="store_true",
  default=False,
  help="Accept the EULA")
parser.add_option(
  "--AWS_ACCESS_KEY_ID",
  dest="AWS_ACCESS_KEY_ID",
  help="AWS Access Key ID")
parser.add_option(
  "--AWS_SECRET_ACCESS_KEY",
  dest="AWS_SECRET_ACCESS_KEY",
  help="AWS Secret Access Key")
parser.add_option(
  "-d",
  "--data",
  dest="data",
  metavar="FILE or -",
  help="AWS credential data.  Path to file containing AWS credentials, or - " \
       "if you want to read the data from stdin.  Format is bash syntax, " \
       "specifying AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
try:
  import boto
  parser.add_option(
    "-b",
    "--use-boto",
    dest="use_boto",
    action="store_true",
    default="false",
    help="Use AWS credentials from default boto configuration")
except ImportError:
  pass # Boto is optional.  Hide CLI option if boto not installed
parser.add_option(
  "--opt-out-of-data-collection",
  dest="optOutOfDataCollection",
  action="store_true",
  default=False,
  help="Opt out of data collection")

# Implementation

def updateCredentialsFromFile(fp, credentials = {}):
  """ Read credentials from file """
  for line in fp:
    if line:
      (key, _, value) = line.strip().partition("=")
      if key.strip() == "AWS_ACCESS_KEY_ID":
        credentials["aws_access_key_id"] = value.strip()
      elif key.strip() == "AWS_SECRET_ACCESS_KEY":
        credentials["aws_secret_access_key"] = value.strip()


def updateCredentialsFromBoto(credentials = {}):
  """ Read credentials from Boto configuration """
  if boto.config.has_section("Credentials"):
    if boto.config.has_option("Credentials", "aws_access_key_id"):
      credentials["aws_access_key_id"] = boto.config.get("Credentials", "aws_access_key_id")
    else:
      # TODO No boto aws access key id
      pass
    if boto.config.has_option("Credentials", "aws_secret_access_key"):
      credentials["aws_secret_access_key"] = boto.config.get("Credentials", "aws_secret_access_key")
    else:
      # TODO No boto aws secret key
      pass
  else:
    # TODO No boto credentials section...
    pass


def handle(options, args):
  """ `grok credentials` handler.  Extracts credentials from command-line
  interface, updates Grok server using web API. """
  try:
    server = args.pop(0)
  except IndexError:
    parser.print_help(sys.stderr)
    sys.exit(1)

  if not options.acceptEULA:
    print >> sys.stderr, (
            "Please read and accept the product End User License Agreement "
            "(EULA) before proceeding.\n"
            "The EULA can be found here: "
            "https://aws.amazon.com/marketplace/agreement?asin=B00I18SNQ6\n\n"
            "To accept the EULA, re-run this command with the "
            "--accept-eula option.")
    sys.exit(1)

  credentials = {
    "aws_access_key_id": options.AWS_ACCESS_KEY_ID,
    "aws_secret_access_key": options.AWS_SECRET_ACCESS_KEY
  }

  if options.data:
    if options.data.strip() == "-":
      updateCredentialsFromFile(sys.stdin, credentials)
    elif options.data:
      with open(options.data, "r") as fp:
        updateCredentialsFromFile(fp, credentials)
  elif options.use_boto:
    updateCredentialsFromBoto(credentials)

  if not (credentials["aws_access_key_id"] and
          credentials["aws_secret_access_key"]):
    parser.print_help(sys.stderr)
    sys.exit(1)

  usertrack = {
    "optin": "false" if options.optOutOfDataCollection else "true"
  }

  grok = GrokSession(server=server)
  grok.apikey = grok.verifyCredentials(**credentials)
  grok.updateSettings(settings=credentials, section="aws")
  grok.updateSettings(settings=usertrack, section="usertrack")
  print grok.apikey


if __name__ == "__main__":
  handle(*parser.parse_args())
