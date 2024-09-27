# Infrastructure as Code

## Organization

To manage both `dev` and `prod` environments in the same AWS account, it's common to separate them using different VPCs. This approach ensures complete isolation between environments. Below is a best practices directory structure and file contents according to the most current Terraform standards and recommendations.

By initializing Terraform separately for each environment, you can manage your dev and prod environments independently. This setup allows you to maintain separate state files and configurations, ensuring that changes in one environment do not affect the other.

## IAM

An IAM role and an instance profile are related but distinct concepts in AWS. Here's a detailed explanation of each and their differences:

### IAM Role

- **Purpose**: An IAM role is an AWS identity with permissions policies that determine what the identity can and cannot do in AWS. Roles are intended to be assumable by trusted entities, such as IAM users, applications, or AWS services like EC2.
- **Use Case**: Roles are used to grant permissions to entities that do not have long-term credentials (e.g., applications running on EC2 instances).
- **Components**: An IAM role consists of a trust policy (which specifies who can assume the role) and one or more permissions policies (which specify what actions are allowed).

### Instance Profile

- **Purpose**: An instance profile is a container for an IAM role that you can use to pass role information to an EC2 instance when the instance starts.
- **Use Case**: Instance profiles are used to associate an IAM role with an EC2 instance, allowing the instance to assume the role and obtain temporary security credentials.
- **Components**: An instance profile contains a reference to an IAM role. When you launch an EC2 instance with an instance profile, the instance can assume the role specified in the profile.

### Key Differences

- **Role**: Defines permissions and trust relationships. It can be assumed by various entities, including EC2 instances, Lambda functions, and other AWS services.
- **Instance Profile**: Specifically used to pass an IAM role to an EC2 instance. It acts as a bridge between the EC2 instance and the IAM role.

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.9 |
| aws | ~> 5.6 |
| tls | ~> 4.0 |

## Providers

| Name | Version |
|------|---------|
| aws | 5.67.0 |
| tls | 4.0.6 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_db_instance.icb](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_instance) | resource |
| [aws_db_subnet_group.icb](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_subnet_group) | resource |
| [aws_dynamodb_table.ichrisbirch_terraform_state_locking](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table) | resource |
| [aws_eip.ichrisbirch_elastic_ip](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/eip) | resource |
| [aws_eip_association.ichrisbirch_elastic_ip_assoc](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/eip_association) | resource |
| [aws_iam_group.developer](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_group) | resource |
| [aws_iam_group.developer_admin](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_group) | resource |
| [aws_iam_group.security](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_group) | resource |
| [aws_iam_group_membership.developer](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_group_membership) | resource |
| [aws_iam_group_membership.developer_admin](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_group_membership) | resource |
| [aws_iam_group_policy_attachment.developer_admin_assume_admin](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_group_policy_attachment) | resource |
| [aws_iam_group_policy_attachment.developer_admin_assume_terraform](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_group_policy_attachment) | resource |
| [aws_iam_group_policy_attachment.developer_cloud_developer](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_group_policy_attachment) | resource |
| [aws_iam_group_policy_attachment.developer_ec2_instance_connect](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_group_policy_attachment) | resource |
| [aws_iam_group_policy_attachment.developer_pass_webserver_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_group_policy_attachment) | resource |
| [aws_iam_group_policy_attachment.security_assume_adming](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_group_policy_attachment) | resource |
| [aws_iam_instance_profile.ichrisbirch_webserver](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_instance_profile) | resource |
| [aws_iam_openid_connect_provider.github](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_openid_connect_provider) | resource |
| [aws_iam_policy.access_backups_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_policy.access_webserver_keys](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_policy.allow_pass_webserver_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_policy.assume_admin_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_policy.assume_terraform_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_policy.cloud_developer](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_policy.ec2_instance_connect](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_policy.terraform_execution](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_policy) | resource |
| [aws_iam_role.admin](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role.github_actions](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role.ichrisbirch_webserver](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role.terraform](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role_policy_attachment.admin_access_webserver_keys](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.admin_administrator_access](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.admin_view_cost_and_usage](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.github_actions_terraform_execution](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.terraform_role_terraform_execution](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.webserver_access_backups_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_role_policy_attachment.webserver_access_webserver_keys](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role_policy_attachment) | resource |
| [aws_iam_user.chris_birch](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_user) | resource |
| [aws_iam_user.john_kundycki](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_user) | resource |
| [aws_iam_user_login_profile.chris_birch](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_user_login_profile) | resource |
| [aws_iam_user_policy_attachment.chris_birch_iam_user_change_password](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_user_policy_attachment) | resource |
| [aws_iam_user_policy_attachment.john_kundycki_iam_user_change_password](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_user_policy_attachment) | resource |
| [aws_instance.ichrisbirch_webserver](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/instance) | resource |
| [aws_internet_gateway.prod](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/internet_gateway) | resource |
| [aws_main_route_table_association.prod_public](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/main_route_table_association) | resource |
| [aws_network_interface.ichrisbirch_webserver](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/network_interface) | resource |
| [aws_route53_record.api_ichrisbirch_a](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.api_ichrisbirch_ns](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.api_ichrisbirch_ns_ns](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.docs_ichrisbirch_a](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.docs_ichrisbirch_cname](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.docs_ichrisbirch_ns](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.ichrisbirch_ns](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_record.www_ichrisbirch_a](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_record) | resource |
| [aws_route53_zone.api_ichrisbirch](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_zone) | resource |
| [aws_route53_zone.docs_ichrisbirch](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_zone) | resource |
| [aws_route53_zone.ichrisbirch](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route53_zone) | resource |
| [aws_route_table.prod_private](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route_table) | resource |
| [aws_route_table.prod_public](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route_table) | resource |
| [aws_route_table_association.prod_private](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route_table_association) | resource |
| [aws_route_table_association.prod_public](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/route_table_association) | resource |
| [aws_s3_bucket.ichrisbirch_backups](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket) | resource |
| [aws_s3_bucket.ichrisbirch_stats](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket) | resource |
| [aws_s3_bucket.ichrisbirch_terraform](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket) | resource |
| [aws_s3_bucket.ichrisbirch_webserver_keys](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket) | resource |
| [aws_s3_bucket_lifecycle_configuration.ichrisbirch_backups](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_lifecycle_configuration) | resource |
| [aws_s3_bucket_policy.ichrisbirch_webserver_keys_admin_role_only_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_policy) | resource |
| [aws_s3_bucket_public_access_block.ichrisbirch_backups](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_public_access_block) | resource |
| [aws_s3_bucket_public_access_block.ichrisbirch_stats](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_public_access_block) | resource |
| [aws_s3_bucket_public_access_block.ichrisbirch_terraform](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_public_access_block) | resource |
| [aws_s3_bucket_public_access_block.ichrisbirch_webserver_keys](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_public_access_block) | resource |
| [aws_security_group.ichrisbirch_database](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group) | resource |
| [aws_security_group.ichrisbirch_webserver](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group) | resource |
| [aws_subnet.prod_private](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/subnet) | resource |
| [aws_subnet.prod_public](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/subnet) | resource |
| [aws_vpc.prod](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc) | resource |
| [aws_vpc_security_group_egress_rule.allow_all_traffic_out](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_egress_rule) | resource |
| [aws_vpc_security_group_egress_rule.postgres_out_all_vpc](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_egress_rule) | resource |
| [aws_vpc_security_group_ingress_rule.allow_all_http_ipv4_in](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_ingress_rule) | resource |
| [aws_vpc_security_group_ingress_rule.allow_all_icmp_ipv4_in](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_ingress_rule) | resource |
| [aws_vpc_security_group_ingress_rule.allow_all_ssh_ipv4_in](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_ingress_rule) | resource |
| [aws_vpc_security_group_ingress_rule.allow_all_tls_ipv4_in](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_ingress_rule) | resource |
| [aws_vpc_security_group_ingress_rule.allow_postgres_from_webserver](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_security_group_ingress_rule) | resource |
| [aws_ami.ichrisbirch_webserver](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ami) | data source |
| [aws_availability_zones.available](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/availability_zones) | data source |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_iam_policy.admin](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy) | data source |
| [aws_iam_policy.billing](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy) | data source |
| [aws_iam_policy_document.assume_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [tls_certificate.github_actions](https://registry.terraform.io/providers/hashicorp/tls/latest/docs/data-sources/certificate) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| db\_password | The password for the database | `string` | n/a | yes |
| db\_username | The username for the database | `string` | n/a | yes |
| gh\_actions\_token\_url | URL for the Github Actions API | `string` | `"https://token.actions.githubusercontent.com"` | no |
| gh\_org | Name of the Github Organization. | `string` | `"datapointchris"` | no |
| gh\_repo | Name of the ECR Repository- should match the Github repo name. | `string` | `"ichrisbirch"` | no |
| private\_subnet\_cidrs | Private Subnet CIDR values | `list(string)` | ```[ "10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24" ]``` | no |
| public\_subnet\_cidrs | Public Subnet CIDR values | `list(string)` | ```[ "10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24" ]``` | no |
| region | The AWS region to deploy resources | `string` | `"us-east-2"` | no |
| vpc\_cidr | The CIDR block for the VPC | `string` | `"10.0.0.0/16"` | no |

## Outputs

| Name | Description |
|------|-------------|
| aws\_account\_id | n/a |
| aws\_region | n/a |
| db\_endpoint | n/a |
| db\_engine | n/a |
| db\_engine\_version | n/a |
| db\_id | n/a |
| db\_instance\_class | n/a |
| db\_security\_group\_ids | n/a |
| db\_subnet\_group\_name | n/a |
| dynamodb\_terraform\_state\_locking\_table\_id | n/a |
| iam\_group\_developer\_admin\_arn | n/a |
| iam\_group\_developer\_arn | n/a |
| iam\_group\_security\_arn | n/a |
| iam\_instance\_profile\_ichrisbirch\_webserver\_arn | n/a |
| iam\_oidc\_provider\_github\_arn | n/a |
| iam\_policy\_access\_webserver\_keys\_arn | n/a |
| iam\_policy\_allow\_pass\_webserver\_role\_arn | n/a |
| iam\_policy\_assume\_admin\_role\_arn | n/a |
| iam\_policy\_assume\_terraform\_role\_arn | n/a |
| iam\_policy\_cloud\_developer\_arn | n/a |
| iam\_policy\_ec2\_instance\_connect\_arn | n/a |
| iam\_policy\_terraform\_execution\_arn | n/a |
| iam\_role\_admin\_arn | n/a |
| iam\_role\_github\_actions\_arn | n/a |
| iam\_role\_ichrisbirch\_webserver\_arn | n/a |
| iam\_role\_terraform\_arn | n/a |
| iam\_user\_chris\_birch\_arn | n/a |
| iam\_user\_john\_kundycki\_arn | n/a |
| internet\_gateway\_id | n/a |
| network\_interface\_ichrisbirch\_webserver\_id | n/a |
| prod\_private\_route\_table\_id | n/a |
| prod\_private\_subnet\_ids | n/a |
| prod\_public\_route\_table\_id | n/a |
| prod\_public\_subnet\_ids | n/a |
| prod\_vpc\_cidr\_block | n/a |
| prod\_vpc\_id | n/a |
| route53\_api\_ichrisbirch\_zone\_id | n/a |
| route53\_api\_ichrisbirch\_zone\_name | n/a |
| route53\_api\_ichrisbirch\_zone\_name\_servers | n/a |
| route53\_api\_ichrisbirch\_zone\_primary\_name\_server | n/a |
| route53\_docs\_ichrisbirch\_zone\_id | n/a |
| route53\_docs\_ichrisbirch\_zone\_name | n/a |
| route53\_docs\_ichrisbirch\_zone\_name\_servers | n/a |
| route53\_docs\_ichrisbirch\_zone\_primary\_name\_server | n/a |
| route53\_ichrisbirch\_zone\_id | n/a |
| route53\_ichrisbirch\_zone\_name | n/a |
| route53\_ichrisbirch\_zone\_name\_servers | n/a |
| route53\_ichrisbirch\_zone\_primary\_name\_server | n/a |
| security\_group\_ichrisbirch\_webserver\_id | n/a |
| user\_chris\_birch\_generated\_password | n/a |
| webserver\_ami\_id | n/a |
| webserver\_availability\_zone | n/a |
| webserver\_elastic\_ip | n/a |
| webserver\_iam\_instance\_profile | n/a |
| webserver\_id | n/a |
| webserver\_instance\_type | n/a |
| webserver\_key\_name | n/a |
| webserver\_route\_table\_id | n/a |
| webserver\_security\_groups | n/a |
| webserver\_subnet\_id | n/a |
<!-- END_TF_DOCS -->
