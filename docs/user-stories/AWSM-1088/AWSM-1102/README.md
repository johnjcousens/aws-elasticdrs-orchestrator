# AWSM-1102: Create Step Functions DR Orchestrator Workflow

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1102

**Type:** Story  
**Status:** To Do  
**Priority:** Medium  
**Assignee:** Prasad Duvvi  
**Reporter:** Chris Falk  
**Labels:** DisasterRecovery  
**Created:** December 09, 2025  
**Last Updated:** January 14, 2026 at 02:45 PM

---

## Description

**Description**

As a DR Operations Engineer, I want a Step Functions workflow that orchestrates complete DR operations, so that failover, failback, and testing are automated and auditable.

**Acceptance Criteria**

- - *Given* DR operation request (failover/failback/test)   *When* initiating the orchestrator workflow   *Then* workflow executes resource discovery, wave orchestration, and validation

- - *Given* orchestrator execution   *When* errors occur   *Then* automatic retries with exponential backoff are attempted

- - *Given* orchestrator execution   *When* manual intervention is required   *Then* workflow pauses and sends notification

**Definition of Done**

- Step Functions state machine created for DR orchestrator

- Workflow supports failover, failback, and test modes

- Error handling and retry logic implemented

- Execution history and audit trail available

- Workflow tested with mock resources

---

## Subtasks (6)

| Key | Summary | Status |
|-----|---------|--------|
| [AWSM-1277](https://healthedge.atlassian.net/browse/AWSM-1277) | Create subnet mapping configuration | To Do |
| [AWSM-1278](https://healthedge.atlassian.net/browse/AWSM-1278) | Implementation - Lambda - Core IP Mapping & DRS Correlation Logic | To Do |
| [AWSM-1279](https://healthedge.atlassian.net/browse/AWSM-1279) | Update DynamoDB table with IP mapping | To Do |
| [AWSM-1280](https://healthedge.atlassian.net/browse/AWSM-1280) | Update DRS Launch Configuration | To Do |
| [AWSM-1291](https://healthedge.atlassian.net/browse/AWSM-1291) | Apply mandatory EC2 instance tags and apply to source servers in DRS | To Do |
| [AWSM-1292](https://healthedge.atlassian.net/browse/AWSM-1292) | Implement - DRS - Workload - "Create extended source servers"  | In Progress |

