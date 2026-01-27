# AWSM-1108: Implement Resource Discovery Caching with Configurable TTL

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1108

**Type:** Story  
**Status:** In Review  
**Priority:** Medium  
**Assignee:** Venkata Kommuri  
**Reporter:** Chris Falk  
**Labels:** DisasterRecovery  
**Created:** December 09, 2025  
**Last Updated:** January 15, 2026 at 10:59 AM

---

## Description

**Description**

As a DR Operations Engineer, I want discovered resource inventory cached with configurable TTL, so that orchestration workflows execute faster without repeated discovery.

**Acceptance Criteria**

- - *Given* resource discovery execution   *When* discovery completes   *Then* inventory is cached in DynamoDB with timestamp

- - *Given* cached inventory   *When* cache age is less than configurable TTL   *Then* cached inventory is used instead of re-discovery

- - *Given* cached inventory   *When* cache age exceeds configurable TTL   *Then* fresh discovery is performed and cache is updated

- - *Given* TTL configuration   *When* updating TTL value   *Then* new TTL takes effect without code changes

**Definition of Done**

- DynamoDB table created for inventory cache

- Cache read/write logic implemented

- Configurable TTL parameter in Systems Manager Parameter Store

- Cache invalidation mechanism implemented

- Performance improvement measured and documented

