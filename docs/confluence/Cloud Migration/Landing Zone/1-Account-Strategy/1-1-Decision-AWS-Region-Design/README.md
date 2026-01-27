# 1-1-Decision-AWS-Region-Design

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867065153/1-1-Decision-AWS-Region-Design

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on September 18, 2025 at 09:07 PM

---

---

title: 1.1 Decision AWS Region Design
-------------------------------------

**Purpose**
-----------

Each customer will need to choose the region or regions to deploy Landing Zone Accelerator on AWS. Consider the following when choosing your region(s).

**Evaluating Regions for deployment**
-------------------------------------

The AWS Cloud is an ever-growing network of Regions and points of presence (PoP), with a global network infrastructure that connects them together. With such a vast selection of Regions, costs, and services available, it can be challenging for organizations to select the optimal Region for a workload. This decision must be made carefully, as it has a major impact on compliance, cost, performance, and services available for your workloads.

There are four main factors that play into evaluating each AWS Region for a workload deployment:

1. **Compliance.** If your workload contains data that is bound by local regulations, then selecting the Region that complies with the regulation overrides other evaluation factors. This applies to workloads that are bound by data residency laws where choosing an AWS Region located in that country is mandatory.
2. **Latency.** A major factor to consider for user experience is latency. Reduced network latency can make substantial impact on enhancing the user experience. Choosing an AWS Region with close proximity to your user base location can achieve lower network latency. It can also increase communication quality, given that network packets have fewer exchange points to travel through.
3. **Cost.** AWS services are priced differently from one Region to another. Some Regions have lower cost than others, which can result in a cost reduction for the same deployment.
4. **Services and features.** Newer services and features are deployed to Regions gradually. Although all AWS Regions have the same service level agreement (SLA), some larger Regions are usually first to offer newer services, features, and software releases. Smaller Regions may not get these services or features in time for you to use them to support your workload.

Evaluating all these factors can make the decision process complicated. This is where your priorities as a business should influence the decision.

**Assess potential Regions for the right option**
-------------------------------------------------

Evaluate by shortlisting potential Regions.

* Check if these Regions are compliant and have the services and features you need to run your workload using the [AWS Regional Services](https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/) website.
* Check feature availability of each service and versions available, if your workload has specific requirements.
* Calculate the cost of the workload on each Region using the [AWS Pricing Calculator](https://calculator.aws/).
* [Test the network latency](https://docs.aws.amazon.com/whitepapers/latest/best-practices-deploying-amazon-workspaces/how-to-check-latency-to-the-closest-aws-region.html) between your user base location and each AWS Region.
* If applicable, reference the supported regions that are documented [here](https://docs.aws.amazon.com/controltower/latest/userguide/region-how.html) for guidance on Control Tower region deployment.

Decision
--------

HealthEdge will deploy their landing zone to the following regions:

| **Role** | **Region** | **Rationale** |
| --- | --- | --- |
| Control Tower Home Region | us-east-1 | This region is closest in proximity to HealthEdge data centers and primary operations. It also offers the broadest AWS service availability and faster adoption of new services and features compared to other east coast regions. This region will serve as the primary region for customers in the eastern US. |
| Secondary Region | us-east-2 | This region will serve as the DR region to us-east-1. |
| Secondary Region | us-west-1 | This region will serve as the DR region to us-west-2. |
| Secondary Region | us-west-2 | This region will serve as the primary region for customers in the western US. |