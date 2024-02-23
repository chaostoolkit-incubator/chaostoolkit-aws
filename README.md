<h2 align="center">
  <br>
  <p align="center"><img src="https://avatars.githubusercontent.com/u/32068152?s=200&v=4"></p>
</h2>

<h4 align="center">AWS extension for the Chaos Toolkit</h4>

<p align="center">
   <a href="https://pypi.org/project/chaostoolkit-aws/">
   <img alt="Release" src="https://img.shields.io/pypi/v/chaostoolkit-aws.svg">
   <a href="#">
   <img alt="Build" src="https://github.com/chaostoolkit-incubator/chaostoolkit-aws/actions/workflows/build-and-test.yaml/badge.svg">
   <a href="https://github.com/chaostoolkit-incubator/chaostoolkit-aws/issues">
   <img alt="GitHub issues" src="https://img.shields.io/github/issues/chaostoolkit-incubator/chaostoolkit-aws?style=flat-square&logo=github&logoColor=white">
   <a href="https://github.com/chaostoolkit-incubator/chaostoolkit-aws/blob/master/LICENSE.md">
   <img alt="License" src="https://img.shields.io/github/license/chaostoolkit-incubator/chaostoolkit-aws">
   <a href="#">
   <img alt="Python version" src="https://img.shields.io/pypi/pyversions/chaostoolkit-aws.svg">
   <a href="https://pkg.go.dev/github.com/chaostoolkit-incubator/chaostoolkit-aws">
</p>

<p align="center">
  <a href="https://join.slack.com/t/chaostoolkit/shared_invite/zt-22c5isqi9-3YjYzucVTNFFVIG~Kzns8g">Community</a> •
  <a href="https://github.com/chaostoolkit-incubator/chaostoolkit-aws/blob/master/CHANGELOG.md">ChangeLog</a>
</p>

---

Welcome to the Amazon Web Services (AWS) extension for Chaos Toolkit. The
package aggregates activities to target your AWS infrastructure and explore
your resilience via Chaos Engineering experiments.

## Install

This package requires Python 3.8+

To be used from your experiment, this package must be installed in the Python
environment where [chaostoolkit][] already lives.

```
$ pip install -U chaostoolkit-aws
```

## Usage

To use the probes and actions from this package, add the following to your
experiment file:

```json
{
    "name": "stop-an-ec2-instance",
    "provider": {
        "type": "python",
        "module": "chaosaws.ec2.actions",
        "func": "stop_instance",
        "arguments": {
            "instance_id": "i-123456"
        }
    }
},
{
    "name": "create-a-new-policy",
    "provider": {
        "type": "python",
        "module": "chaosaws.iam.actions",
        "func": "create_policy",
        "arguments": {
            "name": "mypolicy",
            "path": "user/Jane",
            "policy": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:ListAllMyBuckets",
                            "s3:GetBucketLocation"
                        ],
                        "Resource": "arn:aws:s3:::*"
                    }
                ]
            }
        }
    }
}
```

Or select one at random from an AZ:


```json
{
    "name": "stop-an-ec2-instance-in-az-at-random",
    "provider": {
        "type": "python",
        "module": "chaosaws.ec2.actions",
        "func": "stop_instance",
        "arguments": {
            "az": "us-west-1"
        }
    }
}
```

That's it!

Please explore the code to see existing probes and actions.

## Configuration

### Credentials

This extension uses the [boto3][] library under the hood. This library expects
that you have properly [configured][creds] your environment to connect and
authenticate with the AWS services.

[boto3]: https://boto3.readthedocs.io
[creds]: https://boto3.readthedocs.io/en/latest/guide/configuration.html

#### Use default profile from `~/.aws/credentials` or `~/.aws/config`

This is the most basic case, assuming your `default` profile is properly
[configured][default] in `~/.aws/credentials` (or `~/.aws/config`),
then you do not need to pass any specific credentials to the experiment.

[default]: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#shared-credentials-file

#### Use a non-default profile from `~/.aws/credentials` or `~/.aws/config`

Assuming you have configure a profile in your `~/.aws/credentials`
(or `~/.aws/config`) file, you may declare it in your experiment as follows:

```json
{
    "configuration": {
        "aws_profile_name": "dev"
    }
}
```

Your `~/.aws/credentials` should look like this:

```
[dev]
aws_access_key_id = XYZ
aws_secret_access_key = UIOPIY
```

Or, your `~/.aws/config` should look like this:

```
[profile dev]
output = json
aws_access_key_id = XYZ
aws_secret_access_key = UIOPIY
```

#### Assume an ARN role from a non-default profile

Assuming you have configure a profile in your `~/.aws/config` file with
a specific [ARN role][role] you want to assume during the run:

[role]: https://boto3.readthedocs.io/en/latest/guide/configuration.html#aws-config-file

```json
{
    "configuration": {
        "aws_profile_name": "dev"
    }
}
```

Your `~/.aws/config` should look like this:

```
[default]
output = json

[profile dev]
role_arn = arn:aws:iam::XXXXXXX:role/role-name
source_profile = default
```

#### Assume an ARN role from within the experiment

You mays also assume a role by declaring the role ARN in the experiment
directly. In that case, the profile has no impact if you also set it.

```json
    "configuration": {
        "aws_assume_role_arn": "arn:aws:iam::XXXXXXX:role/role-name",
        "aws_assume_role_session_name": "my-chaos"
    }
```

The `aws_assume_role_session_name` key is optional and will be set to
`"ChaosToolkit"` when not provided.

When this approach is used, the extension performs a [assume role][assumerole]
call against the [AWS STS][sts] service to fetch credentials dynamically.

[assumerole]: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sts.html#STS.Client.assume_role
[sts]: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp_request.html

#### Pass credentials explicitely

You can pass the credentials as a secret to the experiment definition as
follows:

```json
{
    "secrets": {
        "aws": {
            "aws_access_key_id": "your key",
            "aws_secret_access_key": "access key",
            "aws_session_token": "token",
        }
    }
}
```
Note that the token is optional.

Then, use it as follows:

```json
{
    "name": "stop-an-ec2-instance",
    "provider": {
        "type": "python",
        "module": "chaosaws.ec2.actions",
        "func": "stop_instance",
        "secrets": ["aws"],
        "arguments": {
            "instance_id": "i-123456"
        }
    }
}
```

[sources]: https://boto3.readthedocs.io/en/latest/guide/configuration.html#configuring-credentials

### Setting the region

In additon to the authentication credentials, you must configure the region
against which you want to use.

You can either declare it at the top level of the experiment, add:

```json
{
    "configuration": {
        "aws_region": "us-east-1"
    }
}
```

or

```json
{
    "configuration": {
        "aws_region": {
            "type": "env",
            "key": "AWS_REGION"
        }
    }
}
```

But you can also simply set either `AWS_REGION` or `AWS_DEFAULT_REGION` in
your terminal session without declaring anything in the experiment.

If none of these are set, your experiment will likely fail.

## Contribute

If you wish to contribute more functions to this package, you are more than
welcome to do so. Please, fork this project, write unit tests to cover the proposed changes,
implement the changes, ensure they meet the formatting standards by running
`pdm run format` and `pdm run lint`.

The Chaos Toolkit projects require all contributors must sign a
[Developer Certificate of Origin][dco] on each commit they would like to merge
into the master branch of the repository. Please, make sure you can abide by
the rules of the DCO before submitting a PR.

[dco]: https://github.com/probot/dco#how-it-works

### Develop

If you wish to develop on this project, make sure to install the development
dependencies. First installk [PDM](https://pdm-project.org/latest/).

```console
$ pdm install --dev
```

Now, you can edit the files and they will be automatically be seen by your
environment, even when running from the `chaos` command locally.

### Tests

To run the tests for the project execute the following:

```console
$ pdm run test
```

### Formatting and Linting

We use [ruff][ruff] to lint and format the code.

[ruff]: https://github.com/astral-sh/ruff

Before raising a Pull Request, we recommend you run formatting against your code with:

```console
$ pdm run format
```

This will automatically format any code that doesn't adhere to the formatting standards.

As some things are not picked up by the formatting, we also recommend you run:

```console
$ pdm run lint
```

To ensure that any unused import statements/strings that are too long, etc. are also picked up.

### Add new AWS API Support

Once you have setup your environment, you can start adding new
[AWS API support][awsapi] by adding new actions, probes and entire sub-packages
for those.

[awsapi]: https://boto3.readthedocs.io/en/latest/reference/services/index.html

#### Services supported by boto

This package relies on [boto3][] to wrap the API calls into a fluent Python
API. Some newer AWS services are not yet available in boto3, in that case,
you should read the next section.

[boto3]: https://boto3.readthedocs.io/en/latest/reference/services/index.html

Let's say you want to support a new action in the EC2 sub-package.

Start by creating a new function in `ec2/actions.py`:

```python
from chaoslib.types import Configuration, Secrets

from chaosaws import aws_client
from chaosaws.types import AWSResponse

def reboot_instance(instance_id: str, dry_run: bool=False,
                    configuration: Configuration=None,
                    secrets: Secrets=None) -> AWSResponse:
    """
    Reboot a given EC2 instance.
    """
    client = aws_client('ec2', configuration, secrets)
    return client.reboot_instances(InstanceIds=[instance_id], DryRun=dry_run)
```

As you can see, the actual code is straightforward. You first create a
[EC2 client][ec2client] and simply call the appropriate method on that client
with the expected arguments. We return the action as-is so that it can be
logged by the chaostoolkit, or even be used as part of a steady-state
hypothesis probe (if this was a probe, not action that is).

You could decide to make more than one AWS API call but, it is better to keep
it simple so that composition is easier from the experiment. Nonetheless,
you may also compose those directly into a single action as well for specific
use-cases.

Please refer to the Chaos Toolkit documentation to learn more about the
[configuration][] and [secrets][] objects.

[ec2client]: https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#client
[configuration]: http://chaostoolkit.org/reference/api/experiment/#configuration
[secrets]: http://chaostoolkit.org/reference/api/experiment/#secrets

Once you have implemented that action, you must create at least one unit test
for it in the `tests/ec2/test_ec2_actions.py` test module. For example:

```python
from chaosaws.ec2.actions import reboot_instancex

@patch('chaosaws.ec2.actions.aws_client', autospec=True)
def test_reboot_instance(aws_client):
    client = MagicMock()
    aws_client.return_value = client
    inst_id = "i-1234567890abcdef0"
    response = reboot_instance(inst_id)
    client.reboot_instances.assert_called_with(
        InstanceIds=[inst_id], DryRun=False)
```

By using the [built-in Python module to mock objects][pymock], we can mock the
EC2 client and assert that we do indeed call the appropriate method with the right
arguments. You are encouraged to write more than a single test for various
conditions.

[pymock]: https://docs.python.org/3/library/unittest.mock.html#module-unittest.mock

Finally, should you choose to add support for a new AWS API resource altogether,
you should create the according sub-package.

#### Services not supported by boto (new AWS features)

If the support you want to provide is for a new AWS service that [boto][] does
not support yet, this requires direct call to the API endpoint via the
[requests][] package. Say we have a new service, not yet supported by boto3

[eks]: https://aws.amazon.com/eks/
[boto]: https://boto3.readthedocs.io/en/latest/index.html
[requests]: http://docs.python-requests.org/en/master/

```python
from chaoslib.types import Configuration, Secrets

from chaosaws import signed_api_call
from chaosaws.types import AWSResponse

def terminate_worker_node(worker_node_id: str,
                          configuration: Configuration=None,
                          secrets: Secrets=None) -> AWSResponse:
    """
    Terminate a worker node.
    """
    params = {
        "DryRun": True,
        "WorkerNodeId.1": worker_node_id
    }
    response = signed_api_call(
        'some-new-service-name', path='/2018-01-01/worker/terminate',
        method='POST', params=params,
        configuration=configuration, secrets=secrets)
    return response.json()
```

Here is an example on existing API call (as a more concrete snippet):

```python
from chaoslib.types import Configuration, Secrets

from chaosaws import signed_api_call

def stop_instance(instance_id: str, configuration: Configuration=None,
                  secrets: Secrets=None) -> str:
    response = signed_api_call(
        'ec2',
        configuration=configuration,
        secrets=secrets,
        params={
            "Action": "StopInstances",
            "InstanceId.1": instance_id,
            "Version": "2013-06-15"
        }
    )

    # this API returns XML, not JSON
    return response.text
```

When using the `signed_api_call`, you are responsible for the right way of
passing the parameters. Basically, look at the AWS documentation for each
API call.

**WARNING:** It should be noted that, whenever boto3 implements an API, this
package should be updated accordingly, as boto3 is much more versatile and
solid.

#### Make your new sub-package discoverable

Finally, if you have created a new sub-package entirely, you need to make its
capability discoverable by the chaos toolkit. Simply amend the `discover`
function in the `chaosaws/__init__.py`. For example, assuming a new `eks`
sub-package, with actions and probes:

```python
    activities.extend(discover_actions("chaosaws.eks.actions"))
    activities.extend(discover_probes("chaosaws.eks.probes"))
```

