# Migration Tasks -  Customers

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5047910440/Migration%20Tasks%20-%20%20Customers

**Created by:** Raphael Titus on August 26, 2025  
**Last modified by:** Chris Falk on September 03, 2025 at 05:27 PM

---

**This was a working document left in place as a reference but is DEPRECATED. See the** [**Refined Messaging document**](https://healthedgetrial.sharepoint.com/:w:/s/AWSCloudMigration/EYB8cbDBUA5Dj9NMdJfnHYoBUvoGv4mU9K9bo2IOu2Ieew?e=mRauD5) **as a reference.**

| **Timeline** | **Phase** | **Customer Activities** | **Owner** |
| --- | --- | --- | --- |
| T-90 | Initial Communication | 1. Attend customer kickoff call, agenda:     1. Benefits of migrating to AWS for the customer    2. Overview of migration process and milestones, migration dates    3. What will change (DNS, firewall, VPN, deploys, etc.)    4. Identify any key risks early 2. Confirm migration date feasibility and commit 3. Review FAQ 4. Communicate the coming change from hard coded IPs to DNS and start process for any needed firewall changes 5. Provide customer contacts for AWS Migration, specific people and contact information (testing, networking, security, change management, etc.), confirm their availability throughout the process 6. If applicable, start VPN tunnel and direct connectivity implementation process 7. Engage with third party integrations about migration dates and identify required changes 8. Establish project management cadence and escalation path (check-in calls, etc.) |  |
| T-60 | Migration Readiness | 1. Test network connectivity - direct and VPN as applicable 2. Review and iterate test plans for cutovers 3. Initiate third party integration change management processes and cutover plans |  |
| T-30 | Planning | 1. Initiate change management processes on customer side 2. Answer customer-facing questions that arise during wave planning phase 3. Attend Go/No-Go call for migration in the wave 4. Accept and forward calendar invites for cutover and testing events 5. Perform final validation on all network connectivity 6. Confirm resource availability for cutover and testing |  |
| T-20 | Build | 1. Answer customer-facing questions that arise during the wave build phase (minimal) |  |
| T-10 | Infra Testing | 1. Answer customer-facing questions that arise during the wave infrastructure testing phase (minimal) |  |
| T-0 | Cutover & Testing | 1. Perform end to end application testing within the allocated timeline (two weeks non-prod, one week pre-prod, one week prod) 2. Accept and sign off on each cutover 3. Perform customer-side post migration support |  |