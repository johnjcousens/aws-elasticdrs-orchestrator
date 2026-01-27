# AWSM-1106: Implement CLI-Triggered DR Operations with Customer/Environment Scoping

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1106

**Type:** Story  
**Status:** To Do  
**Priority:** Medium  
**Assignee:** Prasad Duvvi  
**Reporter:** Chris Falk  
**Labels:** DisasterRecovery  
**Created:** December 09, 2025  
**Last Updated:** January 07, 2026 at 11:15 AM

---

## Description

**Description**

As a DR Operations Engineer, I want to initiate DR operations via CLI commands with Customer and Environment parameters, so that operations integrate with existing runbooks and can be scoped to specific customer environments.

**Acceptance Criteria**

- - *Given* AWS CLI access   *When* executing DR failover command   *Then* Step Functions orchestrator workflow is initiated

- - *Given* CLI execution   *When* providing operation parameters (mode, scope, Customer, Environment, approval)   *Then* parameters including Customer, Environment, and dr:x tags are validated and passed to orchestrator workflow

- - *Given* CLI execution with Customer and Environment scope   *When* workflow starts   *Then* only resources matching specified Customer, Environment, and dr:x tags are processed

- - *Given* CLI execution   *When* workflow starts   *Then* execution ARN is returned for tracking

**Definition of Done**

- CLI command examples documented with Customer, Environment, and dr:x tag parameters

- SSM document created for DR operations with scoping support

- Parameter validation implemented including Customer, Environment, and dr:x tags

- Execution tracking guidance provided

- Runbook includes CLI usage examples with scoping scenarios

