# AWSM-1104: Implement Lifecycle Orchestration Workflow with Customer/Environment Scoping

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1104

**Type:** Story  
**Status:** In Progress  
**Priority:** Medium  
**Assignee:** Prasad Duvvi  
**Reporter:** Chris Falk  
**Labels:** DisasterRecovery  
**Created:** December 09, 2025  
**Last Updated:** January 15, 2026 at 11:03 AM

---

## Description

**Description**

As a DR Operations Engineer, I want a lifecycle workflow that manages individual resource recovery with Customer and Environment scoping, so that each resource type has appropriate recovery logic and operations can be scoped to specific customer environments.

**Acceptance Criteria**

- - *Given* a resource to recover with Customer and Environment tags   *When* lifecycle workflow executes   *Then* appropriate recovery module is invoked based on resource type

- - *Given* Customer and Environment scope parameters   *When* lifecycle workflow executes   *Then* only resources matching the specified scope are processed

- - *Given* resource recovery   *When* recovery completes   *Then* resource health is validated before marking complete

- - *Given* resource recovery failure   *When* retries are exhausted   *Then* failure is logged and parent workflow is notified

**Definition of Done**

- Lifecycle Step Functions state machine created

- Customer and Environment scoping logic implemented

- Resource type routing logic implemented

- Health validation integrated

- Error propagation to parent workflow configured

- Integration tests with multiple resource types and scoping scenarios

