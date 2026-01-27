# AWSM-1224: Clean up tags for existing production servers - replace DRS with drs:enabled=true

**Jira Link:** https://healthedge.atlassian.net/browse/AWSM-1224

**Type:** Task  
**Status:** Done  
**Priority:** Medium  
**Assignee:** Sudhanshu Saurav  
**Reporter:** Chris Falk  
**Labels:** disasterrecovery  
**Created:** December 19, 2025  
**Last Updated:** January 16, 2026 at 09:52 AM

---

## Description

Review the   and   documents.

For all HRP AD servers in the HRPProduction account that are already implemented, replace  `DRS=True` with  `dr:enabled=false` . AD servers do not need DRS.

For any other HRP production EC2 servers, review whether DRS is required and add tags per the documentation if necessary.

Provide a report in this ticket of the changes that were made for review.

It’s possible there are no production servers yet outside of partner AD servers that will even need DRS enabled.

