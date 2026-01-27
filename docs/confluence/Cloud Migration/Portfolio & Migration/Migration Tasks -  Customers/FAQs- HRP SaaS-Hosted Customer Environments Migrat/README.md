# FAQs: HRP SaaS-Hosted Customer Environments Migration to AWS

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5077926145/FAQs%3A%20HRP%20SaaS-Hosted%20Customer%20Environments%20Migration%20to%20AWS

**Created by:** Brijesh Singh on September 08, 2025  
**Last modified by:** Brijesh Singh on September 17, 2025 at 04:03 PM

---

1. What does it mean for us as a customer?

   1. You will have the same number of environments, with the same capabilities and architecture. HealthEdge will also ensure that the system’s performance matches what you are getting on-prem.
   2. New site-to-site VPNs will be set up between your data center and HealthEdge’s AWS setup. Upon migration of all the environments to AWS old VPNs between your datacenter and HealthEdge’s on-prem data centers will be decommissioned.
   3. All the URLs currently consisting of NAT’d IP addresses will have DNS. You will no longer receive a URL with an IP address.
   4. Healthedge will provide new Environment handoff documents with new URLs.
   5. HealthEdge will provide IP ranges ahead of time and you can allow outbound communication on the IP ranges ahead of time. During the migration, HealthEdge will provide specific list of IP and ports for you to tightly control the outbound and inbound communication.
2. Will I see any change in the license fees or environment Price?

   1. No, the license fees will change due to the AWS migration. The current environment price will also not change. Any new environment Pricing may change in the future.
3. Will there be any impact on DW replication?

   1. No, there will be no impact on DW replication. As part of the migration, you will need to allow connectivity from the new DW server's IP address. The HealthEdge network team will also have to update the firewall to make outbound communication to the customer’s DW target. The network connectivity is set up, the DW replication will continue as is.
4. Will I need to make firewall changes on my end?

   1. Yes, as part of this migration IP addresses of all the servers will change. As a result, you will have to make changes on your end to allow outbound communication to HRP servers. The HealthEdge network team will have to do the same to allow inbound traffic.
5. Will there be any impact on RSO/SSO integration?

   1. No, there will be no impact on RSO/SSO. However, we do need to make network changes on both your end and HealthEdge’s end to allow the new Application servers' IPs to communicate with your AD or LDAP servers. HealthEdge Team will provide the new source IPs.
6. Will there be any impact on third-party integrations?

   1. All third-party integrations will continue to function as they are. However, we will have to make network/firewall changes to ensure that the new Application servers' IPs can communicate with the third-party applications.
7. Will there be any change to SFTP?

   1. Yes, there will be new SFTP servers. User names and passwords will remain the same. The HealthEdge team will document and provide new connection details in the environment Handoff document.

      1. FOR AWS TEAM - Can ALB route the traffic based on source IP and user name?
8. What do I need to tell my vendors?

   1. If you have vendors accessing HRP UI, you will have to provide a new HRP client to the vendors. Also, if your vendors are accessing Connector web-services, SFTP, or Primary DW, you will need to provide new URLs, SFTP servers, and DW hostname to your vendors. The HealthEdge team will provide these details in the environment handoff document.
9. How will I access the primary DW using the RO account?

   1. The IP address of DW servers will change. If you are controlling the outbound communication by IP and Ports, you will need to work with your network team to allow communication to the new DW IP on the same port as 1433 (SQLServer) or 1521 (Oracle).
10. Will there be new URLs for WebUI?

    1. No, the WebUI URLs will be the same.
11. Will authentication change as part of the migration?

    1. No, HealthEdge will preserve all user IDs and passwords. Also, the entire environment, along with the databases, will be migrated, and you will have the same database as the on-prem environment.
12. How will the migration plan look?

    1. If you have standard six Payer environments – Dev, Test, Config, UAT, Preprod, and Prod – the migration will happen in 4 rounds. In the first round, we will migrate two lower-level environments, such as Dev and Test. In the second round, we will migrate an additional two lower-level environments, such as Config and UAT. In the third round, we will migrate Preprod, and Production will be migrated in the fourth and final round. We will apply any lessons learned from the migration of the first two environments to the migration of the next set of environments.
    2. While communication will begin a few months in advance, the actual migration of environments will start and finish within eight weeks. Your feedback throughout the migration process will help us continually improve the process. Your Account Executive and Customer Success Manager will be your primary point of contact during this migration.
13. How will the migration to AWS impact my upgrades if I am in the middle of an upgrade?
14. When will the production environment migrate to AWS?

    1. Production environment will migrate to AWS over the weekend. The activity will start at some point on Friday and finish on Saturday. HealthEdge will communicate the progress periodically throughout the migration process. Additionally, HealthEdge will provide all the changes/ necessary details related to the Production environment in advance for you to communicate to your teams and make the necessary changes on your end.
    2. Please note that all access points will be updated to use DNS instead of IP addresses.
15. What level of testing will HealthEdge perform after migrating the environments to AWS and before handing over the environments to us?

    1. First, HealthEdge will perform an operational health check to ensure that all components of the application are healthy and functioning in AWS. Additionally, HealthEdge will also perform some basic level of functional testing to ensure that basic functionalities such as WebUI, claims search, member search, RSO integration etc. work fine after the migration.
16. What level of testing is required of my team?
17. Can I fall back to on-premises environments during the migration?

    1. Yes, in extreme circumstances where AWS environments are not functioning and are blocking your critical project, HealthEdge will work with you to understand the situation and assist with the next steps. Technically, falling back to on-prem environments is possible.