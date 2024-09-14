# Domain Names

Hosted in `AWS Route 53`  
There are 3 hosted zones, one for the top level domain and one for each subdomain.

## ichrisbirch.com Hosted Zone

This is referred to as the `Apex` domain, or top level domain.

There are 5 records in this hosted zone:

| Record Name          | Type    | Description                                   | Value                    |
| -------------------- | ------- | --------------------------------------------- | ------------------------ |
| ichrisbirch.com      | `NS`    | Created automatically with the hosted zone    | AWS Apex Nameservers     |
| ichrisbirch.com      | `SOA`   | Created automtaically with the hosted zone    | AWS DNS                  |
| api.ichrisbirch.com  | `NS`    | Nameservers from hosted zone `NS` record      | AWS API Nameservers      |
| docs.ichrisbirch.com | `CNAME` | Re-direct from Github Pages to docs subdomain | datapointchris.github.io |
| \www.ichrisbirch.com | `A`     | Points to the EC2 IP of the webserver         | EC2 IP (Elastic IP)      |

## api.ichrisbirch.com Hosted Zone

There are 3 records in this hosted zone:

| Record Name         | Type  | Description                                | Value                 |
| ------------------- | ----- | ------------------------------------------ | --------------------- |
| api.ichrisbirch.com | `A`   | Points to the EC2 IP of the webserver      | EC2 IP (Elastic IP)   |
| api.ichrisbirch.com | `NS`  | Created automatically with the hosted zone | AWS Api Nameservers   |
| api.ichrisbirch.com | `SOA` | Created automtaically with the hosted zone | AWS DNS               |

## docs.ichrisbirch.com Hosted Zone

There are 3 records in this hosted zone:

| Record Name          | Type  | Description                                | Value                 |
| -------------------- | ----- | ------------------------------------------ | --------------------- |
| docs.ichrisbirch.com | `A`   | Points to the EC2 IP of the webserver      | Github Servers        |
| docs.ichrisbirch.com | `NS`  | Created automatically with the hosted zone | AWS Docs Nameservers  |
| docs.ichrisbirch.com | `SOA` | Created automtaically with the hosted zone | AWS DNS               |

Refer to the [Documentation](documentation.md) and [CICD](cicd.md) pages for setting up Github Pages with this subdomain.

!!! tip ""
    Use `dig {address}` to see if the domain looks set up correctly.

!!! danger WARNING
    If the DNS seems to not be updating and the records are not working, be wary of the `Browser Cache` and history!!  
    `Safari` kept the old `IP` in the cache until restart, the only way to see the update was to use a `Private Window`  
    ***Check the cache*** before troubleshooting.

### Apex - `ichrisbirch.com ( www.ichrisbirch.com )`

There should be a `nameserver` record created with the `hosted zone`, and the `soa` is created automatically.  
The `A` record should point to the elastic IP if assigned, or public ip of the instance or load balancer and the name should have subdomain `www`.  *I believe* because the domain `ichrisbirch.com` is the apex, it doesn't need an `A` record.

### `api.ichrisbirch.com`

There should be a `nameserver` record created with the `hosted zone` and `soa`, same as the Apex.  
The `A` record should point to the elastic IP.

!!! caution ""
    There should be another `NS` record with the **`API Nameservers`** that is attached to the Apex zone.
    This allows the Apex to know how to discover the subdomain.

### `docs.ichrisbirch.com`

The docs are slightly different because they are hosted by `github`, being served with `mkdocs`, so they are not sitting on the server like the app (www) and api (api) are.  
There should be the similar `NS` and `soa` records created.  

!!! important ""
    The `A` record points to the `github` (I think) hosts where the docs are hosted:
    ```
    "185.199.108.153",
    "185.199.109.153",
    "185.199.110.153",
    "185.199.111.153"
    ```
    The `CNAME` record lives at the `Apex` level, in place of the `NS` records like the `api` uses.  
    Since the `CNAME` is an alias, it is used to alias `docs.ichrisbirch.com` => `datapointchris.github.io`

## Reference

### 1. NS (Name Server) Records

**Purpose:** NS records specify the authoritative name servers for a domain. These servers hold the DNS records for the domain.
**Function:** Direct traffic by telling DNS resolvers which nameserver(s) to ask for the specific domain’s information.
**Usage:** Found at the domain's DNS zone and commonly points to multiple nameservers to provide redundancy.
**Example:**

```txt
example.com. IN NS ns1.example.com.
example.com. IN NS ns2.example.com.
```

### 2. SOA (Start of Authority) Records

**Purpose:** SOA records provide essential information about the DNS zone of a domain, including the primary nameserver, the admin’s contact email, and timing information for zone transfers.
**Function:** Defines the authoritative server and sets the rules for DNS caching, zone transfers, and DNS record updates.
**Usage:** Should be the first record in a DNS zone file, as it contains critical operational data.
**Example:**

```txt
example.com. IN SOA ns1.example.com. hostmaster.example.com. (
              2023010101 ; Serial
              7200       ; Refresh
              3600       ; Retry
              1209600    ; Expire
              3600       ; Minimum TTL
              )
```

### 3. A (Address) Records

**Purpose:** A records map a domain or subdomain to an IPv4 address.
**Function:** Translates the human-readable domain names to numerical IP addresses that computers use.
**Usage:** Essential for pointing a domain or subdomain to a web server’s IP address.
**Example:**

`www.example.com. IN A 192.0.2.1`

### 4. CNAME (Canonical Name) Records

**Purpose:** CNAME records alias one domain name to another.
**Function:** Points one domain/subdomain to another domain/subdomain, allowing management of multiple addresses by changing a single target address.
**Usage:** Useful for pointing multiple subdomains to a single canonical name and to reduce redundancy in DNS management.
**Example:**

`blog.example.com. IN CNAME www.example.com.`

### How They Relate to Domains and Subdomains

**NS Records:** Define which servers are authoritative for the domain's DNS records. If you have subdomains, the NS records for the main domain affects them unless specifically overridden.

**SOA Records:** Hold administrative information and control parameters for the DNS zone; they are vital for overall DNS zone health and updates.

**A Records:** Directly tie domain names and subdomains to specific IP addresses. Different subdomains can be mapped to different IPs using A records.

**CNAME Records:** Allow you to point subdomains (or even the root domain if needed) to other domain names, simplifying DNS management. For example, blog.example.com can point to `www.example.com`, which has an A record, thereby inheriting its IP indirectly.

**Example Application:**
For a domain example.com:

- **NS Records:** Point to ns1.example.com and ns2.example.com.
- **SOA Record:** Contains administrative details for the DNS zone, like contact info and timing settings.
- **A Record:** Points `www.example.com` to 192.0.2.1.
- **CNAME Record:** Points blog.example.com to `www.example.com`, which has the A record for the actual IP.

### AWS Documentation

[Routing traffic for subdomains - Amazon Route 53Routing traffic for subdomains - Amazon Route 53](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-routing-traffic-for-subdomains.html)
