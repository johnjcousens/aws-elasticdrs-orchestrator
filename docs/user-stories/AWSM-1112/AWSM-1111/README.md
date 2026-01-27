# AWSM-1111: Implement DRS Orchestration Module

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1111

**Type:** Story  
**Status:** In Progress  
**Priority:** Medium  
**Assignee:** John Cousens  
**Reporter:** Chris Falk  
**Labels:** DisasterRecovery  
**Created:** December 09, 2025  
**Last Updated:** January 20, 2026 at 10:56 AM

---

## Description

**Description**

As a DR Operations Engineer, I want integration with AWS DRS service using AllowLaunchingIntoThisInstance for failover and failback, so that critical workloads achieve 15-30 minute RTO with pre-provisioned instances and preserved instance identity.

**Acceptance Criteria**

- - *Given* EC2 instances tagged with dr:recovery-strategy=drs   *When* initiating recovery   *Then* DRS recovery jobs are created for tagged instances

- - *Given* pre-provisioned DR region instances   *When* initiating failover   *Then* AllowLaunchingIntoThisInstance is used to launch into pre-provisioned instances

- - *Given* primary-DR instance pairs   *When* identifying target instances   *Then* Name tags are matched between primary and DR region instances

- - *Given* failback operation   *When* returning to primary region   *Then* AllowLaunchingIntoThisInstance is used to launch into original source instances

- - *Given* DRS recovery job   *When* job is in progress   *Then* job status is monitored and reported

- - *Given* DRS recovery completion   *When* instances are launched   *Then* instance IDs and status are captured for validation

**Definition of Done**

- DRS API integration implemented with AllowLaunchingIntoThisInstance support

- Name tag matching logic for primary-DR instance pairs

- Recovery job creation logic for failover and failback

- Job status monitoring implemented

- Error handling for DRS API failures

- Integration tests with DRS service and pre-provisioned instances

