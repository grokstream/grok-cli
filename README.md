Grok Command Line Interface
===========================

This repository contains the Grok Command line interface (CLI). `grokcli` allows you to easily interact with a Grok server through the command line including creating instances, etc.

In addition you can use `grokcli` to integrate with third party applications.  Included in `grokcli` is an integration with Datadog (see [Grok Integration With Datadog](docs/Grok-Integration-with-DataDog.pdf) for full details). See more details by running `python -m grokcli.datadog --help`.

Installation
------------

Requires: Python (2.6 or greater)

- pip (recommended)

  `pip install grokcli`

- easy_install

  `easy_install grokcli`

- setup.py

  `python setup.py install`

Usage
-----

Grok CLI tools provides a single, high-level `grok` command, from which
a number of sub-commands can be invoked:

    grok [command] [options]

Each command takes `GROK_SERVER_URL` and `GROK_API_KEY` as the first two arguments after the command name. However, if you set those two environment variables, you can omit those arguments from the commands.

- `grok credentials`

  Use the `grok credentials` sub-command to add your AWS credentials to a
  running Grok server configuration:

      grok credentials GROK_SERVER_URL [options]

  The `GROK_SERVER_URL` positional argument is required and must be a url to a
  running Grok server.  For example: https://ec2-AA-BB-CC-DD.us-west-2.compute.amazonaws.com

  You can specify your credentials in one of three ways:

  - Specify `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` CLI options.

    ```
    grok credentials GROK_SERVER_URL --AWS_ACCESS_KEY_ID=... --AWS_SECRET_ACCESS_KEY=...
    ```

  - Read AWS credentials from a specific file using the `-d`, or `--data` CLI
    options.

    ```
    grok credentials GROK_SERVER_URL -d PATH_TO_FILE
    grok credentials GROK_SERVER_URL --data=PATH_TO_FILE
    ```

    You can read from stdin using `-`:

    ```
    grok credentials GROK_SERVER_URL -d - < PATH_TO_FILE
    grok credentials GROK_SERVER_URL --data=- < PATH_TO_FILE
    ```

    The credentials file should be formatted according to this template:

    ```
    AWS_ACCESS_KEY_ID=Your AWS access key ID here
    AWS_SECRET_ACCESS_KEY=Your AWS secret access key here
    ```

  - Use existing boto configuration.

    ```
    grok credentials GROK_SERVER_URL --use-boto
    ```

- `grok export`

  Export Grok model definitions to a file in JSON or YAML format.

      grok export [GROK_SERVER_URL GROK_API_KEY] [options]

  The `GROK_SERVER_URL` positional argument is required and must be a url to a
  running Grok server.  For example: https://ec2-AA-BB-CC-DD.us-west-2.compute.amazonaws.com

  The `GROK_API_KEY` positional argument is also required, and can be retrieved
  from the web interface of a running Grok server.

  By default, `grok export` prints output to stdout, which can be directed to a
  file:

      grok export [GROK_SERVER_URL GROK_API_KEY] > file.json

  However, you can optionally specify a file using the `-o` or `--output` CLI
  option:

      grok export [GROK_SERVER_URL GROK_API_KEY] -o file.json
      grok export [GROK_SERVER_URL GROK_API_KEY] --output=file.json

  Use the `-y` or `--yaml` CLI flag to save output in YAML format

      grok export [GROK_SERVER_URL GROK_API_KEY] -y
      grok export [GROK_SERVER_URL GROK_API_KEY] --yaml

- `grok import`

  Import Grok model definitions into a Grok server from a local file.

      grok import [GROK_SERVER_URL GROK_API_KEY] [FILE] [options]

  The `GROK_SERVER_URL` positional argument is required and must be a url to a
  running Grok server.  For example: https://ec2-AA-BB-CC-DD.us-west-2.compute.amazonaws.com

  The `GROK_API_KEY` positional argument is also required, and can be retrieved
  from the web interface of a running Grok server. The API Key is synonymous with the mobile
  password.

  The `FILE` positional argument is optional, however if it is not specified,
  `grok import` will assume `STDIN` if `-d` or `--data` is not specified.  The
  following are equivalent:

      grok import [GROK_SERVER_URL GROK_API_KEY] file.json
      grok import [GROK_SERVER_URL GROK_API_KEY] < file.json
      grok import [GROK_SERVER_URL GROK_API_KEY] -d file.json
      grok import [GROK_SERVER_URL GROK_API_KEY] --data=file.json

  `grok import` supports files in YAML format, if pyyaml is installed and
  available on the system.

- `grok (DELETE|GET|POST)`

  Included in the Grok CLI tool is a lower-level direct API which translates
  CLI options to direct HTTP calls into the Grok web service.  For example, to
  get all available cloudwatch metrics:

      grok GET GROK_SERVER_URL/_metrics/cloudwatch GROK_API_KEY

  For `grok POST` and `grok DELETE`, where request data may be required, such
  data can be specified either via the `-d`, or `--data` CLI option, or
  supplied via STDIN:

      grok POST GROK_SERVER_URL/_models GROK_API_KEY < model-definition.json
      grok POST GROK_SERVER_URL/_models GROK_API_KEY -d model-definition.json
      grok POST GROK_SERVER_URL/_models GROK_API_KEY --data model-definition.json

- `grok metrics`

  Manage monitored metrics.

      grok metrics (list|unmonitor) [GROK_SERVER_URL GROK_API_KEY] [options]

  To get a list of monitored metrics:

      grok metrics [GROK_SERVER_URL GROK_API_KEY]

  Limiting to monitored metrics for a specific AWS instance:

      grok metrics list [GROK_SERVER_URL GROK_API_KEY] --instance=INSTANCE_ID --region=REGION --namespace=NAMESPACE

  To unmonitor a metric:

      grok metrics unmonitor https://localhost CmHnD --id=METRIC_ID

- `grok instances`

  Manage monitored instances.

      grok instances (list|unmonitor) [GROK_SERVER_URL GROK_API_KEY] [options]

  To get a list of all monitored instances:

      grok instances list [GROK_SERVER_URL GROK_API_KEY]

  To unmonitor an instance:

      grok instances unmonitor [GROK_SERVER_URL GROK_API_KEY] --id=INSTANCE_ID

- `grok cloudwatch`

  Manage CloudWatch metrics.

      grok cloudwatch (metrics|instances) (list|monitor|unmonitor) [GROK_SERVER_URL GROK_API_KEY] [options]

  To list available cloudwatch metrics:

      grok cloudwatch metrics list [GROK_SERVER_URL GROK_API_KEY]

  To filter list of available cloudwatch metrics by instance id:

      grok cloudwatch metrics list [GROK_SERVER_URL GROK_API_KEY] --instance=INSTANCE_ID

  To monitor a metric (example):

      grok cloudwatch metrics monitor [GROK_SERVER_URL GROK_API_KEY] \
        --metric=CPUUtilization \
        --namespace=AWS/EC2 \
        --region=us-west-2 \
        --dimensions InstanceId i-abc123

  To monitor an instance (example):

      grok cloudwatch instances monitor [GROK_SERVER_URL GROK_API_KEY] \
        --namespace=AWS/EC2 \
        --region=us-west-2 \
        --instance=i-abc123

  To unmonitor a metric (example):

      grok cloudwatch metrics unmonitor [GROK_SERVER_URL GROK_API_KEY] \
        --metric=CPUUtilization \
        --namespace=AWS/EC2 \
        --region=us-west-2 \
        --dimensions InstanceId i-abc123

  To unmonitor an instance (example):

      grok cloudwatch instances unmonitor [GROK_SERVER_URL GROK_API_KEY] \
        --namespace=AWS/EC2 \
        --region=us-west-2 \
        --instance=i-abc123

- `grok custom`

  Manage custom metrics.

  To list available custom metrics:

      grok custom metrics list [GROK_SERVER_URL GROK_API_KEY]

  To monitor a custom metric:

      grok custom metrics monitor [GROK_SERVER_URL GROK_API_KEY] --id=METRIC_ID

  To unmonitor a custom metric:

      grok custom metrics unmonitor [GROK_SERVER_URL GROK_API_KEY] --name=METRIC_NAME

- `grok autostacks`

  Manage autostacks.

  To create an autostack:

      grok autostacks stacks create [GROK_SERVER_URL GROK_API_KEY] --name=NAME --region=REGION --filters='{"tag:FILTER_NAME": ["FILTER_VALUE"]}'

  You can use any AWS tag for FILTER_NAME. The FILTER_VALUE is an AWS-specific
  wildcard, not a full-fledged regular expression. * matches any number of characters
  and ? matches any single character. The filter name and value are both
  case-sensitive.

  For example, "jenkins-*" and "jenkins-??????" both match "jenkins-master".

  You can use any AWS tag for the first component of a filter, though for
  optimal performance we recommend that the first tag/value pair specified be
  the one that eliminates the most instances. Because AWS only supports OR
  operations at this time, we have to implement the AND (intersection) operation
  locally. Our implementation sends the first tag/value to AWS, gets all the
  matching instances, and then filters them against the remaining tag/value
  filters locally.

  This does not create any metrics for the new autostack. You must create metrics
  for the new autostack with grok autostacks metrics add (see below)

  To preview an autostack:

      grok autostacks stacks create [GROK_SERVER_URL GROK_API_KEY] --preview --region=REGION --filters='{"tag:FILTER_NAME": ["FILTER_VALUE"]}'

  To list AutoStacks:

      grok autostacks stacks list [GROK_SERVER_URL GROK_API_KEY]

  To delete an AutoStack:

      grok autostacks stacks delete [GROK_SERVER_URL GROK_API_KEY] --name=STACK_NAME --region=REGION

  or:

      grok autostacks stacks delete [GROK_SERVER_URL GROK_API_KEY] --id=STACK_ID

  To add metric type(s) monitored by an AutoStack:

      grok autostacks metrics add [GROK_SERVER_URL GROK_API_KEY] --name=STACK_NAME --region=REGION --metric_namespace=METRIC_NAMESPACE --metric_name=METRIC_NAME

  or:

      grok autostacks metrics add [GROK_SERVER_URL GROK_API_KEY] --id=STACK_ID --metric_namespace=METRIC_NAMESPACE --metric_name=METRIC_NAME

  To list metric type(s) monitored by an AutoStack:

      grok autostacks metrics list [GROK_SERVER_URL GROK_API_KEY] --name=STACK_NAME --region=REGION

  or:

      grok autostacks metrics list [GROK_SERVER_URL GROK_API_KEY] --id=STACK_ID

  To remove metric type(s) monitored by an AutoStack:

      grok autostacks metrics remove [GROK_SERVER_URL GROK_API_KEY] --name=STACK_NAME --region=REGION --metric_id=METRIC_ID

  or:

      grok autostacks metrics remove [GROK_SERVER_URL GROK_API_KEY] --id=STACK_ID --metric_id=METRIC_ID

  To list EC2 Instances associated with an AutoStack(s):

      grok autostacks instances list [GROK_SERVER_URL GROK_API_KEY] --name=STACK_NAME --region=REGION

  or:

      grok autostacks instances list [GROK_SERVER_URL GROK_API_KEY] --id=STACK_ID

Note to developers
------------------

To add a command, create a python module in
[grokcli/commands/](grokcli/commands) with a `handle()` function which accepts
two arguments: `options`, and `args`.  Register the command by importing the
module in [grokcli/commands/\_\_init\_\_.py](grokcli/commands/__init__.py) and
adding it to `__all__`.

