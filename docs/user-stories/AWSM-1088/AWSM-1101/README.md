# AWSM-1101: Develop Tag-Based Resource Discovery Using AWS Resource Explorer

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1101

**Type:** Story  
**Status:** Done  
**Priority:** Medium  
**Assignee:** Venkata Kommuri  
**Reporter:** Chris Falk  
**Labels:** DisasterRecovery  
**Created:** December 09, 2025  
**Last Updated:** January 14, 2026 at 09:29 AM

---

## Description

**Description**

As a DR Operations Engineer, I want automated discovery of DR-enabled resources using AWS Resource Explorer APIs, so that orchestration workflows efficiently discover tagged resources across accounts and regions without custom cross-account logic.

**Acceptance Criteria**

- - *Given* resources tagged with dr:enabled=true   *When* running resource discovery   *Then* AWS Resource Explorer APIs query tagged resources across multiple accounts and regions

- - *Given* multi-account LZA structure   *When* discovering resources   *Then* Resource Explorer Organizations integration provides cross-account discovery

- - *Given* discovered resources   *When* generating inventory   *Then* inventory includes resource type, ID, tags (including Customer and Environment), account, and region

- - *Given* resource type coverage   *When* validating discovery   *Then* all required resource types are supported: EC2, RDS, EKS, ECS, S3, EFS, FSx, ElastiCache, Route53, ALB/NLB, VPN, Transit Gateway

**Definition of Done**

- AWS Resource Explorer configured with aggregator region for cross-region search

- Resource Explorer Organizations integration enabled for multi-account discovery

- Lambda function implements Resource Explorer API-based discovery

- Discovery supports all required resource types: EC2, RDS, EKS, ECS, S3, EFS, FSx, ElastiCache, Route53, ALB/NLB, VPN, Transit Gateway

- Resource type coverage validated and documented

- Inventory output format defined and documented

- Unit tests cover discovery logic for all resource types

