# AWSM-1107: Configure Cross-Account IAM Roles via LZA

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1107

**Type:** Story  
**Status:** In Review  
**Priority:** Medium  
**Assignee:** Venkata Kommuri  
**Reporter:** Chris Falk  
**Labels:** DecisionRequired, DisasterRecovery  
**Created:** December 09, 2025  
**Last Updated:** January 14, 2026 at 11:58 AM

---

## Description

**Description**

As a Cloud Infrastructure Architect, I want cross-account IAM roles configured for DR orchestration via LZA customizations-config.yaml, so that central DR account can orchestrate resources in workload accounts.

**Acceptance Criteria**

- - *Given* LZA multi-account structure   *When* configuring IAM roles   *Then* DR orchestration role is defined in LZA customizations-config.yaml for deployment to each workload account

- - *Given* DR orchestration role   *When* defining permissions   *Then* least privilege access is granted for DR operations only

- - *Given* cross-account access   *When* assuming roles   *Then* trust relationship validates source account and external ID

**Definition of Done**

- IAM role defined in LZA customizations-config.yaml

- Role configuration includes all workload accounts

- Trust relationships configured and tested

- Permission policies follow least privilege

- Role assumption tested from DR account

- LZA deployment validated

