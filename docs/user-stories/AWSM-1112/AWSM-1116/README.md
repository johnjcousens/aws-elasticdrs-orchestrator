# AWSM-1116: Validate DRS Readiness for Pre-Provisioned Instances

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1116

**Type:** Story  
**Status:** To Do  
**Priority:** Medium  
**Assignee:** John Cousens  
**Reporter:** Chris Falk  
**Labels:** DisasterRecovery  
**Created:** December 09, 2025  
**Last Updated:** January 20, 2026 at 02:52 PM

---

## Description

**Description**

As a DR Operations Engineer, I want DRS readiness validated for pre-provisioned instances, so that failover operations can proceed with confidence.

**Acceptance Criteria**

- - *Given* pre-provisioned DR instances   *When* validating readiness   *Then* AllowLaunchingIntoThisInstance capability is verified

- - *Given* primary-DR instance pairs   *When* validating configuration   *Then* Name tag matching is confirmed between regions

- - *Given* DRS replication   *When* validating readiness   *Then* replication lag is within acceptable thresholds

- - *Given* pre-provisioned instances   *When* validating state   *Then* instances are running without attached storage (cost optimization)

**Definition of Done**

- AllowLaunchingIntoThisInstance validation logic implemented

- Name tag matching validation implemented

- Replication lag threshold checks implemented

- Pre-provisioned instance state validation implemented

- Readiness validation testing completed

