# AWS

## IAM

### Groups

`admin` - Administrator access
`developer` - Access to services

- GROUP: `admin`
  - POLICY: `AWSAdministratorAccess`
- GROUP: `developer` group has POLICIES
  - POLICY: `AllowPassRoleS3DatabaseBackups`
    - Allow to assume the `S3DatabaseBackups` ROLE
      - ROLE: `S3DatabaseBackups` - S3 Full Access
  - POLICY: `AWSKeyManagementServiceUser`
    - Allow to view and use all KMS keys
    - Allow grant to AWSResources (like S3)
  - POLICY: `AmazonRDSFullAccess`
  - POLICY: `AmazonS3FullAccess`
  - POLICY: `AmazonDynamoDBFullAccess`
- ROLE: `AWSTrustedAdvisorRole`

```mermaid
graph TB
    admin[admin - Administrator access]
    developer[developer - Access to services]
    AWSAdministratorAccess[AWSAdministratorAccess]
    AllowPassRoleS3DatabaseBackups[AllowPassRoleS3DatabaseBackups]
    AWSKeyManagementServiceUser[AWSKeyManagementServiceUser]
    AmazonRDSFullAccess[AmazonRDSFullAccess]
    AmazonS3FullAccess[AmazonS3FullAccess]
    AmazonDynamoDBFullAccess[AmazonDynamoDBFullAccess]
    AWSTrustedAdvisorRole[AWSTrustedAdvisorRole]
    S3DatabaseBackups[S3DatabaseBackups - S3 Full Access]
    admin -->|Attached Policy| AWSAdministratorAccess
    developer -->|Attached Policy| AllowPassRoleS3DatabaseBackups
    developer -->|Attached Policy| AWSKeyManagementServiceUser
    developer -->|Attached Policy| AmazonRDSFullAccess
    developer -->|Attached Policy| AmazonS3FullAccess
    developer -->|Attached Policy| AmazonDynamoDBFullAccess
    AllowPassRoleS3DatabaseBackups -.->|Assume Role| S3DatabaseBackups
    style AllowPassRoleS3DatabaseBackups fill:gray,stroke:#333,stroke-width:2px
    style S3DatabaseBackups fill:gray,stroke:#f66,stroke-width:2px,stroke-dasharray: 5, 5
  ```

## EC2

### ichrisbirch instances

US East 1
Security Group: ichrisbirch-sg
Key name: ichrisbirch-webserver
Ubuntu 22.04
