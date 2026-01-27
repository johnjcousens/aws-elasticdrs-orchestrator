# AWSM-1105: Develop Module Factory Pattern

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1105

**Type:** Story  
**Status:** In Progress  
**Priority:** Medium  
**Assignee:** Prasad Duvvi  
**Reporter:** Chris Falk  
**Labels:** DisasterRecovery  
**Created:** December 09, 2025  
**Last Updated:** January 15, 2026 at 11:02 AM

---

## Description

**Description**

As a DR Operations Engineer, I want a module factory that dynamically invokes resource-specific recovery modules, so that new resource types can be added without changing core orchestration.

**Acceptance Criteria**

- - *Given* a resource type (EC2, RDS, EKS, etc.)   *When* module factory is invoked   *Then* appropriate recovery module Lambda function is called

- - *Given* a new resource type   *When* adding support   *Then* new module is registered without modifying factory logic

- - *Given* module execution   *When* module completes   *Then* standardized response format is returned

**Definition of Done**

- Module factory Lambda function implemented

- Module registry configuration created

- Standardized module interface defined

- Example module skeleton implemented

- Documentation for adding new modules

