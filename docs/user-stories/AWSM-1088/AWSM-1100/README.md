# AWSM-1100: Implement Tag Validation with SCPs and Tag Policies

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1100

**Type:** Story  
**Status:** Done  
**Priority:** Medium  
**Assignee:** John Cousens  
**Reporter:** Chris Falk  
**Labels:** DisasterRecovery  
**Created:** December 09, 2025  
**Last Updated:** January 13, 2026 at 09:06 AM

---

## Description

**Description**

As a Cloud Infrastructure Architect, I want automated tag validation enforced via SCPs and tag policies, so that resources are correctly tagged before DR orchestration.

**Acceptance Criteria**

- - *Given* the DR tagging taxonomy   *When* implementing validation rules   *Then* tag policies validate required DR tags are present

- - *Given* tagged resources   *When* tags have invalid values   *Then* SCPs prevent resource creation or modification

- - *Given* non-compliant resource creation attempts   *When* detected by SCPs   *Then* operations are blocked and error messages guide users

**Definition of Done**

- Tag policies deployed for DR tag validation

- SCPs configured to enforce tag requirements

- Tag policies and SCPs tested with compliant and non-compliant resources

- Error messages provide clear guidance for compliance

- Validation rules documented in runbooks

