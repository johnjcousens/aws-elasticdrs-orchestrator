# AWSM-1271: Develop Tag-Based Resource Discovery Using AWS Resource Explorer - Enhancements

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1271

**Type:** Task  
**Status:** In Review  
**Priority:** Medium  
**Assignee:** Venkata Kommuri  
**Reporter:** Prasad Duvvi  
**Labels:** disasterrecovery  
**Created:** January 14, 2026  
**Last Updated:** January 15, 2026 at 10:59 AM

---

## Description

**Description**

As a DR Operations Engineer, I want automated discovery of DR-enabled resources using AWS Resource Explorer APIs, so that orchestration workflows efficiently discover tagged resources across accounts and regions without custom cross-account logic.

**Acceptance Criteria**

- - *Given* resources tagged with dr:enabled=true   *When* running resource discovery   *Then* AWS Resource Explorer APIs query tagged resources across multiple accounts and regions

- - *Given* multi-account LZA structure   *When* discovering resources   *Then* Resource Explorer Organizations integration provides cross-account discovery

- - *Given* discovered resources   *When* generating inventory   *Then* inventory includes resource type, ID, tags (including Customer and Environment), account, and region

- - *Given* resource type coverage   *When* validating discovery   *Then* all required resource types are supported: EC2, RDS, EKS, ECS, S3, EFS, FSx, ElastiCache, Route53, ALB/NLB, VPN, Transit Gateway

This is an enhancement to   

**Definition of Done**

- Fetch private IP & subnet details for each instance tagged for DR

- Update DynamoDb table

