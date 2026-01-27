# AWSM-1118: Create DRS Readiness Report

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1118

**Type:** Story  
**Status:** To Do  
**Priority:** Medium  
**Assignee:** Unassigned  
**Reporter:** Chris Falk  
**Labels:** DisasterRecovery  
**Created:** December 09, 2025  
**Last Updated:** December 09, 2025 at 05:10 PM

---

## Description

**Description**

As a DR Operations Manager, I want automated DRS readiness reports, so that DR readiness status is visible to stakeholders.

**Acceptance Criteria**

- - *Given* DRS source servers   *When* generating readiness report   *Then* report includes replication status, lag, and readiness for all servers

- - *Given* readiness report   *When* servers are not ready   *Then* issues are highlighted with remediation guidance

- - *Given* report generation   *When* scheduled daily   *Then* report is automatically generated and distributed

**Definition of Done**

- Readiness report generation logic implemented

- Report format defined (HTML/PDF)

- Scheduled report generation configured

- Report distribution via email/S3 configured

- Sample reports reviewed and approved

