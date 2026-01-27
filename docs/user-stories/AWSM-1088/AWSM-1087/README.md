# AWSM-1087: Update Existing Tag Documentation with DR Taxonomy

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1087

**Type:** Story  
**Status:** Done  
**Priority:** Medium  
**Assignee:** Chris Falk  
**Reporter:** Chris Falk  
**Labels:** DisasterRecovery  
**Created:** December 09, 2025  
**Last Updated:** December 19, 2025 at 11:58 AM

---

## Description

**Description**

As a Cloud Infrastructure Architect, I want existing tag documentation updated with standardized DR tagging taxonomy, so that resources can be consistently tagged for automated DR orchestration with clearer semantics.

**Acceptance Criteria**

- - *Given* existing tag documentation   *When* updating with DR taxonomy   *Then* standard DR tags are added: dr:enabled, dr:priority, dr:wave, dr:rto-target, dr:rpo-target, dr:recovery-strategy

- - *Given* the DR tagging taxonomy   *When* documenting tag usage   *Then* documentation includes tag definitions, valid values, usage examples, and migration plan from existing DRS tags

- - *Given* multi-tenant requirements   *When* designing the taxonomy   *Then* leverage existing Environment and Customer tags for scoping operations

**Definition of Done**

- Existing tag documentation updated with DR tags

- Migration plan from existing DRS tags to new dr:x taxonomy documented

- Tag validation rules defined (valid values, required vs optional)

- Usage examples provided for common scenarios including Customer and Environment tags

- Documentation reviewed and approved by architecture team

