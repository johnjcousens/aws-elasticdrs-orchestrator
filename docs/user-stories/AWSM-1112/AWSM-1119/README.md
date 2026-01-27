# AWSM-1119: Support AllowLaunchingIntoThisInstance Capability

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1119

**Type:** Story  
**Status:** In Progress  
**Priority:** Medium  
**Assignee:** John Cousens  
**Reporter:** Chris Falk  
**Labels:** DisasterRecovery  
**Created:** December 09, 2025  
**Last Updated:** January 20, 2026 at 02:51 PM

---

## Description

**Description**

As a DR Operations Engineer, I want support for pre-provisioned DR instances with AllowLaunchingIntoThisInstance, so that cost is optimized by pre-provisioning instances with minimal or no storage.

**Acceptance Criteria**

- - *Given* pre-provisioned DR instances   *When* configuring DRS   *Then* AllowLaunchingIntoThisInstance capability is enabled

- - *Given* DRS recovery   *When* launching into pre-provisioned instance   *Then* instance retains instance ID and network configuration

- - *Given* pre-provisioned instances   *When* not in use   *Then* instances run with minimal or no attached storage (cost optimization)

**Definition of Done**

- AllowLaunchingIntoThisInstance configuration implemented

- Pre-provisioned instance setup documented with minimal/no storage guidance

- Recovery into pre-provisioned instances tested

- Cost optimization validated

- Runbook includes pre-provisioning procedures

