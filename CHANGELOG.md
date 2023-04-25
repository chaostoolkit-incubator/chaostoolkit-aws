# Changelog

## [Unreleased][]

[Unreleased]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.23.0...HEAD

## [0.23.0][] - 2023-04-25

[0.23.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.22.1...0.23.0

### Added

- The `get_service_graph` in the XRay package

## [0.22.1][] - 2023-04-17

[0.22.1]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.22.0...0.22.1

### Changed

- Export `get_most_recent_trace` from XRay probes

## [0.22.0][] - 2023-04-16

[0.22.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.21.3...0.22.0

### Added

- Added new probes to retrieve distributed traces from XRay

### Fixed

- Moved away from nosetest setup functions in emr tests

## [0.21.3][] - 2023-02-26
[0.21.3]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.21.2...0.21.3

### Fixed

- fixed format for python miniaml version as per https://github.com/pypa/packaging/issues/673

### Changed
- Added new EC2 probe to check whether minimum number of instances are running

### Added
- Added new probe to check whether Access Logging is enabled at ALB
- Added new action to enable/disable access logging at ALB

## [0.21.2][] - 2022-07-12
[0.21.2]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.21.1...0.21.2

### Fixed

- fixed `chaosaws.s3.controls.upload` region for url

## [0.21.1][] - 2022-07-12
[0.21.1]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.21.0...0.21.1

### Fixed

- fixed `chaosaws.s3.controls.upload` so the url is correctly added

## [0.21.0][] - 2022-07-12
[0.21.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.20.1...0.21.0

### Changed

- Setting the S3 URL into the journal when stored

## [0.20.1][] - 2022-07-11
[0.20.1]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.20.0...0.20.1

### Fixed

- fixed `chaosaws.s3.controls.upload` so it uploads the journal as a file
- fixed `chaosaws.s3.controls.upload` so the timestamp is generated
- changed `chaosaws.s3.controls.upload`, use old style when dumping as YAML


## [0.20.0][] - 2022-07-11
[0.20.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.19.0...0.20.0

### Added

- a control to upload the experiment's journal to a S3 bucket when the
  experiment finishes: `chaosaws.s3.controls.upload`
- removed Python 3.6 support as Chaos Toolkit now requires 3.7

## [0.19.0][] - 2021-12-02
[0.19.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.18.0...0.19.0

### Added
- workflow to mark issues as `stale` and remove them after 7 days of being `stale`
- added `chaosaws.elasticache.actions.test_failover` for testing automatic failover on specified shards 
- adding `put_parameter` to ssm actions
- updated `aws_region` configuration in Readme


## [0.18.0][] - 2021-10-11
[0.18.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.17.0...0.18.0

### Added

- added new variable for cloudwatch probes `get_metric_statistics` and `get_metric_data`
called `dimensions` to allow for multiple dimension queries
- Added `.github/workflows/check_pr.yaml` which checks if a PR has modified the
CHANGELOG.md and if it changed/added tests
- adding s3 probes `bucket_exists`, `object_exists`, & `versioning_status`
- adding s3 actions `delete_object`, `toggle_versioning`
- explicitly support python 3.9

## [0.17.0][]
[0.17.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.16.0...0.17.0

### Added
- adding list_event_source_mapping to awslambda probes
- adding delete_event_source_mapping to awslambda actions
- adding toggle_event_source_mapping_state to awslambda actions
- adding put_metric_data to cloudwatch actions
- added GitHub Actions Workflows for Build and Test, Build and Discover, and Releasing
- added `Makefile` to abstract away common commands: `install`, `install-dev`, `lint`, `format`, `tests`
- added `chaosaws.fis.actions.start_experiment` to start an AWS FIS experiment
- added `chaosaws.fis.actions.stop_experiment` to stop an AWS FIS experiment
- added `chaosaws.fis.probes.get_experiment` to retrieve an AWS FIS experiments details

### Removed
- Removed TravisCI related files
- All `# -*- coding: utf-8 -*-` statements
- Python 3.5 support

### Changed
- update return value of asg action detach_random_instances to include instance IDs
- switch from `pycodestyle` to `black`, `flake8`, and `isort` for linting/formatting
- applied `black`, `flake8`, and `isort` across the codebase
- applied `pyupgrade --py36-plus`

### Fixed
- `chaosaws.route53.probes` now correctly exposes the `__all__` attribute

## [0.16.0][]
[0.16.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.15.1...0.16.0

### Added
- adding route53 probes & actions
- adding ssm actions

### Changed

## [0.15.1][]
[0.15.1]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.15.0...0.15.1

### Changed

- use setuptools auto discovery of all packages under `chaosaws` to not forget
  them anylonger
- turn `chaosaws.emr` into a proper Python package

## [0.15.0][]
[0.15.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.14.0...0.15.0


### Added

- adding probes to rds resource (instance_status, cluster_status, cluster_membership_count)
- add Cloudwatch get_metric_data probe
- adding new probes & actions for EMR
- building for Python 3.8

### Changed

- fixing `describe_cache_cluster` argument calls ordering
- adding actions to ecs resource ('tag_resource', 'untag_resource', 'set_service_placement_strategy', 'set_service_deployment_configuration', & 'update_container_instances_state')

## [0.14.0][]

- added EMR probes 'describe_cluster', 'describe_instance_fleet', 'describe_instance_group', 'list_cluster_fleet_instances', 'list_cluster_group_instances'
- added EMR actions 'modify_cluster', 'modify_instance_fleet', 'modify_instance_groups_instance_count', 'modify_instance_groups_shrink_policy'

[0.14.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.13.0...0.14.0

### Added

- adding elasticache probes `describe_cache_cluster`, `get_cache_node_count`, & `get_cache_node_status`
- add EC2 actions to allow/revoke security group ingress

## [0.13.0][]

[0.13.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.12.0...0.13.0

### Added

- correcting IndexError in ecs are desired tasks running probe
- adding unit tests for are desired tasks running probe
- updating probes ALL list to include describe functions
- adding action to set the desired task count of an ecs service
- updating elbv2 deregister action to include port [#60][60]
- adding probe to asg to report healthy & unhealthy instance counts
- adding utility to breakup large iterables into smaller groups

## [0.12.0][]

[0.12.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.11.2...0.12.0

### Changed

- Clarify the way the client receives the credentials for authentifying with
  AWS services. This change MAY BE BREAKING since we do not assume
  `"us-east-1"` as a default region anymore. You must be be explicit about the
  target region!
  [#57][57]

[57]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/issues/57

### Added

- adding action stop_random_instances to asg actions
- adding describe_auto_scaling_groups to asg probes
- correcting annotation for ec2 probe count_instances
- correcting annotation for timeout parameter in asg actions
- fix tests to match new pytest's API for accessing exceptions' values [#52][52]
- adding action stop_random_tasks to ecs actions
- adding describe_service, describe_tasks, & describe_cluster to ecs probes

[52]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/issues/52

## [0.11.2][]

[0.11.2]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.11.1...0.11.2

### Added

- correcting paginator [#49][49]

[49]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/pull/49

## [0.11.1][]

[0.11.1]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.11.0...0.11.1

### Added

- ensure readme is properly rendered in Pypi

## [0.11.0][]

[0.11.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.10.0...0.11.0

### Added

- adding delete action to elbv2 module
- adding stop db instance action
- adding delete db instance/cluster actions
- adding delete db cluster endpoint action
- adding change_subnets action to asg
- adding has_subnets probe to asg
- adding start_instances and reboot_instances actions to ec2
- adding instance_state probe to ec2
- adding action detach_random_volume to asg
- adding action detach_random_volume to ec2
- adding action reboot_cache_cluster to elasticache
- adding action delete_cache_cluster to elasticache
- adding action delete_replication_group to elasticache

## [0.10.0][]

[0.10.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.9.0...0.10.0

### Added

- adding terminate_instance(s) actions to ec2/actions.py
- asg actions to suspend/resume services
- asg probe to detect if process is suspended
- adding set_security_groups actions to elbv2
- adding set_subnets action to elbv2
- adding optional ability to dynamically assume an AWS role declared in the
  experiment, after assuming the initial aws profile
- adding action to terminate random asg instance(s)
- adding action to detach random instances from autoscaling groups

## [0.9.0][]

[0.9.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.8.0...0.9.0

### Added

-   support for Python 3.7
-   support for cloudwatch probes and actions
-   support for invoking lambdas
-   support for getting and updating lambda timeout and memory size limits
-   probe for cloudwatch metric statistics

## [0.8.0][]

[0.8.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.7.1...0.8.0

### Changed

-   make sure instances with no explicit lifecycle can be stopped. They are
    assumed to be in the `normal` lifecycle as per the last
    [line of the AWS documentation][]. [#25][25]

[25]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/issues/25
[instlifecycledocs]: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-purchasing-options.html

-   add probes to wait for auto-scaling group to have healthy/unhealthy instance
    and a probe to check if there is any ongoing scaling activity

## [0.7.1][]

[0.7.1]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.7.0...0.7.1

### Changed

-   add `elbv2`, `asg` and `awslambda` packages to the setup function so they
    get packaged and distributed

### Added

## [0.7.0][]

[0.7.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.6.0...0.7.0

### Added

-   add `count_instances` probe which can be used to count of all instances matching filters
-   support for elbv2 with basic probes and action
-   support for asg with basic probes
-   fix asg probe to support pagination
-   support for lambda with basic probes and action

### Changed

-   Refactoring to support spot instances termination along with cancelling spot request

## [0.6.0][]

[0.6.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.5.2...0.6.0

### Added

-   Pass filters to `ec2` actions so that specific instances can be selected
    for an experiment

## [0.5.2][]

[0.5.2]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.5.1...0.5.2

### Changed

-   Remove the irrelevant discover system call

## [0.5.1][]

[0.5.1]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.5.0...0.5.1

### Changed

-   Make EKS activities discoverable

## [0.5.0][]

[0.5.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.4.2...0.5.0

### Added

-   EKS API support: create/delete clusters and describe/list clusters
-   Various ECS activities from @cara-puce

## [0.4.2][]

[0.4.2]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.4.1...0.4.2

### Changed

-   Read package version from source file without importing as dependencies may
    not be deployed then

## [0.4.1][]

[0.4.1]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.4.0...0.4.1

### Added

-   MANIFEST.in so that non-source code files are included in source distribution package

## [0.4.0][]

[0.4.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.3.0...0.4.0

### Added

-   Add basic IAM Policy support
-   Add ECS actions to delete services, clusters and container instances

### Changed

-   Stoping EC2 instances may not take an AZ as a parameter to pick
    one or many random instances to stop within that AZ.

## [0.3.0][]

[0.3.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.2.0...0.3.0

### Added

-   Support specifying a specific profile config to assume a role [#5][5]

[5]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/issues/5

## [0.2.0][]

[0.2.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.1.0...0.2.0

### Added

-   Documentation on contributing to the project
-   Adding a function to sign a request when boto3 lacks support for a specific
    AWS API


## [0.1.0][]

[0.1.0]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/tree/0.1.0

### Added

-   Initial release
