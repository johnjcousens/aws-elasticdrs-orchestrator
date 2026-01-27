# AWSM-1109: Create DR Orchestration Configuration Management - Design

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1109

**Type:** Story  
**Status:** In Progress  
**Priority:** Medium  
**Assignee:** Venkata Kommuri  
**Reporter:** Chris Falk  
**Labels:** DisasterRecovery  
**Created:** December 09, 2025  
**Last Updated:** January 14, 2026 at 11:58 AM

---

## Description

**Description**

As a DR Operations Engineer, I want centralized configuration management for DR orchestration parameters, so that settings are consistent and easily updated.

**Acceptance Criteria**

- - *Given* orchestration parameters (timeouts, retries, regions)   *When* storing configuration   *Then* parameters are stored in Systems Manager Parameter Store

- - *Given* environment-specific settings   *When* retrieving configuration   *Then* correct environment parameters are loaded (dev/test/prod)

- - *Given* configuration changes   *When* updating parameters   *Then* changes take effect without code deployment

**Definition of Done**

- Parameter Store hierarchy defined

- Configuration parameters documented

