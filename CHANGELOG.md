# Changelog

## [Unreleased][]

[Unreleased]: https://github.com/chaostoolkit-incubator/chaostoolkit-aws/compare/0.14.0...HEAD

- adding probes to rds resource (instance_status, cluster_status, cluster_membership_count)
- add Cloudwatch get_metric_data probe

## [0.14.0][]

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
