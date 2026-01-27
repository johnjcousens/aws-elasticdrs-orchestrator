# 2-4 Cross Account Deployment Role setup for CD

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5072060443/2-4%20Cross%20Account%20Deployment%20Role%20setup%20for%20CD

**Created by:** Rahul Sharma on September 04, 2025  
**Last modified by:** Rahul Sharma on September 30, 2025 at 10:43 PM

---

Architecture Overview
---------------------

This guide explains the IAM role configuration needed for GitHub Actions to deploy resources across multiple AWS accounts.

Configuration Components
------------------------

### 1. Source Account Setup

* **OIDC Provider Configuration**

  + Configure OIDC provider to establish trust with GitHub Actions
  + Link the OIDC provider with a Deployer IAM role
* **Deployer Role**

  + Create IAM role with trust relationship to OIDC provider
  + Configure necessary permissions for cross-account access

### 2. Target Accounts Setup

Target accounts are configured within the AWS Organization:

* Create Cross-account Deploy role
* Configure trust relationship with Source account's Deployer role
* Set permissions for AWS resource management

![GHAction-CD.drawio_(1).png](images/GHAction-CD.drawio_(1).png)

### 3. GitHub Actions Configuration

* Configure workflow to authenticate using OIDC
* Set up necessary AWS credentials and role assumptions
* Define deployment steps for each environment

Authentication Flow
-------------------

1. GitHub Actions workflow starts
2. OIDC Provider authenticates the workflow
3. Workflow assumes Deployer role in source account
4. Deployer role assumes Cross-account Deploy role in target account
5. Resources are deployed in target account

Required IAM Trust Relationships
--------------------------------

**Source Account Deployer Role Trust Policy:**


```json
{
    "Version": "October 17, 2012",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::<SOURCE-ACCOUNT>:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity"
        }
    ]
}

```


**Target Account Cross-Account Deploy Role Trust Policy:**


```
{
    "Version": "October 17, 2012",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::<SOURCE-ACCOUNT>:role/Deployer"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}

```


This setup enables secure, automated deployments from GitHub Actions to multiple AWS accounts while maintaining proper security controls and account separation.