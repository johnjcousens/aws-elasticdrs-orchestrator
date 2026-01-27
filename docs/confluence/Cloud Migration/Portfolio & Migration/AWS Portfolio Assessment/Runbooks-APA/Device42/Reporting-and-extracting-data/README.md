# Reporting-and-extracting-data

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867098737/Reporting-and-extracting-data

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:52 AM

---

The [Device42 Object Query Language (DOQL)](https://docs.device42.com/device42-doql/) allows you to run queries against the Device42 database and is one of the key differentiators versus “black box” discovery tools on the market. The Data Dictionary, Entity Relationship Diagram and DB Viewer Schema is accessible from the Main Appliance UI as mentioned at the beginning of this document. It’s well worth understanding the basics of DOQL as it’s a powerful tool for building custom reports using the discovered data and any custom fields that you’ve created. DOQL is also the engine which Advanced Reporting is built on and that’s also where you’ll find the integrations to AWS tools.

### AWS Migration Evaluator

You can generate a Device42 AWS [Migration Evaluator report](https://docs.device42.com/reports/aws-migration-evaluator/) from Device42’s predefined reports and upload the report to the AWS Migration Evaluator portal.

### AWS Migration Hub

You can generate a Device42 AWS [Migration Hub report](https://docs.device42.com/reports/aws-migration-hub/) from Device42’s predefined reports and upload the report to the AWS Migration Hub portal.

### AWS Migration Portfolio Assessment (MPA)

You can generate a Device42 AWS MPA report from Device42’s predefined reports and upload the report to the AWS MPA tool. This is not currently documented but the report is available in the Workload Portability folder alongside the AWS Migration Hub report.

### AWS Optimization & Licensing Assessment (OLA)

You can generate a Device42 AWS OLA report from Device42’s predefined reports and send the report to the AWS OLA team for further analysis. This is not currently documented but the report is available in the Workload Portability folder alongside the AWS Migration Hub report.

### AWS Application Migration Service (MGN)

After you have performed your HyperVisors / \*nix/ Windows scans and associated your business applications to your devices using the Device42 Business Application functionality, you are ready to prepare for your migration to AWS using CloudEndure.

Device42 has streamlined the process of conducting cloud migrations to AWS by [integrating with the CloudEndure Blueprint](https://docs.device42.com/reports/cloud-endure-device42/).  With a few short clicks, Device42 users can assess which workloads have the CloudEndure agent loaded as well as export blueprints for CloudEndure migrations.