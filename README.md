# AWS Attack Surface Management
Continuous AWS Attack Surface Discovery of external facing services and Scanning using Nmap. If you look at this in the right angle :stuck_out_tongue:, technically this is an External Vulnerability Analysis at scale in a tight budget.

## Infrastructure
The infrastructure for this project is built with Cloud Development Kit or CDK. The primary reason is the self mutating capability of CDK Pipelines, secondary because the source for AAS Management is built with Python, building Infrastructure in the same language is a huge plus. If you don't have CDK setup locally already before deployment, please refer to the [Official CDK page](https://github.com/aws/aws-cdk) or install by running below command in a terminal.
> npm i -g aws-cdk 

### Components
* CloudWatch Event - Time Based
    * Cron is scheduled to be triggered midnight UTC
* Lambda Functions
    * ASM-1 - Gathers AWS Accounts dynamically from AWS Organizations
	* ASM-2 - Uses boto3 to gather external IP address from _Lightsail, RDS, ELBv1/2, Elasticsearch, Redshift, CloudFront, EC2, Beanstalk, API Gateway_
	* ASM-3(Docker Container) - Image built with nmap to scan the external IP Address from those services.
* Roles
    * The entire project is built over existing Trust Relationship of roles in the respective AWS Accounts. Refer Project `FleetAccess` for more information.
	* Hub Role - present in the Security or Automation Account
	* Org Read Only Role - present in the Billing/AWS Organizations Account with a trust relationship with the Hub Role
	* Spoke Role - present in all AWS Accounts or commonly referred as the fleet, with trust relationthip with the Hub Role.
* VPC
    * Lambda functions are built in a VPC with a private and public subnet.
	* NAT Gateway in the public subnet.
	* Lambda functions in the private subnet routing egress traffic through the NAT Gateway. There are no security groups for ingress, as traffic is not expected.

![CDK Pipelines to deploy the infrastructure for AWS Attack Surface Management](AWS_Attack_Surface_Management.png)

## Workflow
* A time based CloudWatch Event triggers **ASM-1** lambda function which assumes the _org_read_only_role_ in the Billing Account to gather list of AWS Accounts and invokes the **ASM-2** function with the AWS Account IDs as payload.
    * ASM-1 invokes ASM-2 in a _for_ loop passing the AWS Account IDs, essentially making it a asynchronuous invocation of the ASM-2 the n number of times the number of AWS Accounts.
	* For instance if there are 300 AWS Accounts, ASM-1 invokes ASM-2, 300 times with respective AWS Accounts IDs.
* ASM-2 does the heavy lifting of enumerating 10 different AWS Services which could have an external presense.
    * ASM-2 invokes ASM-3 for every external IP Address as payload. 
* ASM-3 is a docker container run in Lambda which has nmap packaged. This is again is asynchronously invoked, meaning ASM-3 is invoked as many times as the external IP Addresses for each service. This is extremely scalable with any number of AWS Accounts and external facing services. After the IP address is scanned accompanied with the `Vulners` scripts`, notifications on information about open ports are sent to a slack channel.


## To be Added _(in the next version)_
* Add capability to store nmap scan results to a S3 bucket, for nmap diffs, so that only changes are reported or notified.
* Add capability to store IP Addresses and open ports information in a DynamoDB Table, so that this informaiton is looked up before notifications, this way same alerts are not sent again. -- Done

## Advanced Architectures
* This setup could be extended to work with industry leading vulnerability management tools such as Rapid7 InsightVM or Qualys, instead of using Nmap for scanning.
* The results could be fed into a SIEM such as Sumologic for further analysis and dashboarding capabilities and further more invoke Security Operations playbooks and detection notifications from Sumo with its integration with Slack and PagerDuty.

## Why not
* Some of the questions I think of, why not just use AWS Inspector's Network Reachability module to help in identifying the open ports. 
The answer is that, it only helps in the case of EC2 instances, the same couldn't be used for public RDS instances or Elasticsearch instances.
* Follow up question to that answer is, why not just alert on those specific API calls when, say a RDS or Elasticsearc instance is made public. 
The answer is not simple, because for one reason, it's cumbersome to find existing public resources, while also some of the API calls are a bit complicated when it comes to identifying if a resource is being made public.