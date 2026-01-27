# AWSM-1113: Implement DRS Drill Mode for Testing

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1113

**Type:** Story  
**Status:** In Progress  
**Priority:** Medium  
**Assignee:** John Cousens  
**Reporter:** Chris Falk  
**Labels:** DisasterRecovery  
**Created:** December 09, 2025  
**Last Updated:** January 20, 2026 at 02:54 PM

---

## Description

**Description**

As a DR Operations Engineer, I want DRS drill mode support for isolated testing, so that DR capabilities are validated without impacting production.

**Acceptance Criteria**

- - *Given* test operation request   *When* initiating DRS recovery   *Then* drill mode is used instead of recovery mode

- - *Given* drill mode execution   *When* instances are launched   *Then* instances are launched in isolated test network

- - *Given* drill completion   *When* test is finished   *Then* drill instances are automatically terminated

**Definition of Done**

- Drill mode parameter added to recovery logic

- Isolated test network configuration defined

- Automatic cleanup logic implemented

- Drill mode tested end-to-end

- Drill mode documented in runbooks

