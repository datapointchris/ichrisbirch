# Domain Names

Hosted in AWS Route 53
There are 3 hosted zones, one for the top level domain and one for each subdomain.

## ichrisbirch.com Hosted Zone

This is referred to as the "apex" domain, or top level domain.

There are 5 records in this hosted zone:

| Record Name          | Type    | Description                                   | Value                    |
| -------------------- | ------- | --------------------------------------------- | ------------------------ |
| ichrisbirch.com      | `NS`    | Created automatically with the hosted zone    | AWS Nameservers          |
| ichrisbirch.com      | `SOA`   | Created automtaically with the hosted zone    | AWS DNS                  |
| api.ichrisbirch.com  | `NS`    | Nameservers from hosted zone `NS` record      | AWS Nameservers          |
| docs.ichrisbirch.com | `CNAME` | Re-direct from Github Pages to docs subdomain | datapointchris.github.io |
| www.ichrisbirch.com  | `A`     | Points to the EC2 IP of the webserver         | EC2 IP (23.22.30.103)    |

## api.ichrisbirch.com Hosted Zone

There are 3 records in this hosted zone:

| Record Name         | Type  | Description                                | Value                 |
| ------------------- | ----- | ------------------------------------------ | --------------------- |
| api.ichrisbirch.com | `A`   | Points to the EC2 IP of the webserver      | EC2 IP (23.22.30.103) |
| api.ichrisbirch.com | `NS`  | Created automatically with the hosted zone | AWS Nameservers       |
| api.ichrisbirch.com | `SOA` | Created automtaically with the hosted zone | AWS DNS               |

## docs.ichrisbirch.com Hosted Zone

There are 3 records in this hosted zone:

| Record Name         | Type  | Description                                | Value                 |
| ------------------- | ----- | ------------------------------------------ | --------------------- |
| docs.ichrisbirch.com | `A`   | Points to the EC2 IP of the webserver      | EC2 IP (23.22.30.103) |
| docs.ichrisbirch.com | `NS`  | Created automatically with the hosted zone | AWS Nameservers       |
| docs.ichrisbirch.com | `SOA` | Created automtaically with the hosted zone | AWS DNS               |

Refer to the [Documentation](documentation.md) and [CICD](cicd.md) pages for setting up Github Pages with this subdomain.

!!! tip
    Use `dig {address}` to see if the domain looks set up correctly.
