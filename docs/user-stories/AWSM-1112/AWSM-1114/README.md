# AWSM-1114: Handle DRS API Rate Limits

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1114

**Type:** Story  
**Status:** In Progress  
**Priority:** Medium  
**Assignee:** John Cousens  
**Reporter:** Chris Falk  
**Labels:** DisasterRecovery  
**Created:** December 09, 2025  
**Last Updated:** January 15, 2026 at 11:04 AM

---

## Description

**Description**

As a DR Operations Engineer, I want DRS API calls to handle rate limits gracefully, so that large-scale recovery operations complete successfully.

**Acceptance Criteria**

- - *Given* DRS API rate limit exceeded   *When* making API calls   *Then* exponential backoff retry logic is applied

- - *Given* multiple concurrent recovery jobs   *When* creating jobs   *Then* job creation is throttled to stay within rate limits

- - *Given* rate limit errors   *When* retries are exhausted   *Then* error is logged and escalated

**Definition of Done**

- Exponential backoff logic implemented

- Rate limit detection and handling implemented

- Throttling mechanism for concurrent jobs

- Rate limit testing performed

- Monitoring for rate limit errors configured

