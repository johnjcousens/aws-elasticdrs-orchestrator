# Define-IDS-via-Landing-Zone-Accelerator

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867034286/Define-IDS-via-Landing-Zone-Accelerator

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:35 AM

---

**Purpose**
-----------

This document describes the process in deploying Security SIEM and IDS services in AWS through the AWS Platform Accelerator.

**Prerequisites**
-----------------

Before deploying out these controls in an AWS environment, it’s important that the following pre-requisites are met.

* The **Region Design page** should be referenced and baselined.

  + Establish region(s) in global-config.yaml
* The **Landing Zone OU Characteristics Design** page should be referenced and baselined.

  + Establish Organization Unit(s) (OU) in organization-config.yaml
* The **Detective Controls design page** should be referenced and baselined.

**Parameter Values**
--------------------

The following parameters are a description of the attributes as well as the allowed values

### Macie

* **enable**: Determine if Amazon Macie is enabled.

  + Type: Boolean
  + Valid Values: `true | false`
* **excludeRegions**: A list of regions to exclude Amazon Macie deployment.

  + Type: List
  + Valid Values: Valid AWS Regions or empty list (e.g. [])
* **policyFindingsPublishingFrequency**: The frequency with which Amazon Macie publishes updates to policy findings for an account. This includes publishing updates to AWS Security Hub and Amazon EventBridge (formerly called Amazon CloudWatch Events).

  + Type: String
  + Valid Values: FIFTEEN\_MINUTES | ONE\_HOUR | SIX\_HOURS
* **publishSensitiveDataFindings:** Determine if findings by Amazon Macie are stored in Amazon Simple Storage (Amazon S3) Bucket.

  + Type**: Boolean**
  + Value Values: `true | false`

### GuardDuty

* **enable:** Determine if AWS GuardDuty is enabled.

  + Type: Boolean
  + Valid Values: `true | false`
* **excludeRegions**: A list of regions to exclude AWS GuardDuty deployment.

  + Type: List
  + Valid Values: Valid AWS Regions or empty list (e.g. [])
* **s3Protection:** This is the Guard Duty Members configuration.

  + **enable:** Determine if S3 protection is enabled.

    - Type: Boolean
    - Valid Values: `true | false`
  + **excludeRegions:** A list of regions to exclude for Amazon S3 Protection.

    - Type: List
    - Valid Values: Valid AWS Regions or empty list (e.g. [])
* **exportConfiguration:** This is the Guard Duty data export configuration.

  + **enable:** Determine if Guard Duty data export configuration is enabled.

    - Type: Boolean
    - Valid Values: `true | false`
  + **destinationType:** Specify the destination type as a data source

    - Type: String
    - Valid Values: S3
  + **exportFrequency:** Specifies how frequently updated findings are exported.

    - Type: String
    - Valid Values: FIFTEEN\_MINUTES | ONE\_HOUR | SIX\_HOURS

**Procedure**

The following is an example of how to establish Amazon Macie, AWS Guard Duty as well as AWS Security Hub in the security-config.yaml