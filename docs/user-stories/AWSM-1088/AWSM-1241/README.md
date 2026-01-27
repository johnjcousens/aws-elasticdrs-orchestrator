# AWSM-1241: Create DR Orchestration Configuration Management - Implementation

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1241

**Type:** Task  
**Status:** To Do  
**Priority:** Medium  
**Assignee:** Venkata Kommuri  
**Reporter:** Prasad Duvvi  
**Labels:** disasterrecovery  
**Created:** January 07, 2026  
**Last Updated:** January 07, 2026 at 11:10 AM

---

## Description

**Description**

As a DR Operations Engineer, I want centralized configuration management for DR orchestration parameters, so that settings are consistent and easily updated.

**Acceptance Criteria**

- - *Given* orchestration parameters (timeouts, retries, regions)   *When* storing configuration   *Then* parameters are stored in Systems Manager Parameter Store

- - *Given* environment-specific settings   *When* retrieving configuration   *Then* correct environment parameters are loaded (dev/test/prod)

- - *Given* configuration changes   *When* updating parameters   *Then* changes take effect without code deployment

**Definition of Done**

- Environment-specific parameters created

- Configuration retrieval logic implemented

- Configuration validation implemented

