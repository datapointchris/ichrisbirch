# Infrastructure as Code

## Organization

To manage both `dev` and `prod` environments in the same AWS account, it's common to separate them using different VPCs. This approach ensures complete isolation between environments. Below is a best practices directory structure and file contents according to the most current Terraform standards and recommendations.

By initializing Terraform separately for each environment, you can manage your dev and prod environments independently. This setup allows you to maintain separate state files and configurations, ensuring that changes in one environment do not affect the other.
