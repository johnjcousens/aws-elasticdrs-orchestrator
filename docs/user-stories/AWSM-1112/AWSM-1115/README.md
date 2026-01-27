# AWSM-1115: Implement DRS Configuration Management (Simplified)

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1115

**Type:** Story  
**Status:** In Progress  
**Priority:** Medium  
**Assignee:** John Cousens  
**Reporter:** Chris Falk  
**Labels:** DisasterRecovery  
**Created:** December 09, 2025  
**Last Updated:** January 20, 2026 at 10:57 AM

---

## Description

**Description**

As a DR Operations Engineer, I want DRS replication settings managed for source servers with simplified configuration given pre-provisioned instances, so that configuration is consistent and recovery behavior is predictable.

**Acceptance Criteria**

- - *Given* DRS replication settings template   *When* applying to source servers   *Then* settings are synchronized across all tagged servers

- - *Given* pre-provisioned DR instances with AllowLaunchingIntoThisInstance   *When* configuring DRS   *Then* launch template synchronization may not be required

- - *Given* primary-DR instance pairs   *When* validating configuration   *Then* Name tag matching is verified between regions

- - *Given* configuration drift   *When* detected   *Then* drift is reported and remediation is triggered

- - *Given* new source servers   *When* added to DRS   *Then* standard configuration is automatically applied

**Definition of Done**

- Configuration template defined for pre-provisioned instance scenario

- Name tag matching validation implemented

- Synchronization logic implemented (simplified for pre-provisioned instances)

- Drift detection implemented

- Automatic remediation configured

- Configuration sync tested with multiple servers

