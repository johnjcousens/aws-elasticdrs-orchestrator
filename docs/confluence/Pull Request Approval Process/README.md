# Pull Request Approval Process

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/GC/pages/3341910050/Pull%20Request%20Approval%20Process

**Created by:** Sivani K (Deactivated) on July 03, 2023  
**Last modified by:** Sivani K (Deactivated) on July 03, 2023 at 05:20 PM

---

Page Owner Abhiram Chennuru (Deactivated), Page Reviewer Kushagra Kumar Tyagi (Deactivated), / Sanjeeva Pendekanti

**Purpose**

Document to outline the PR approval process.

**Scope**

Process of approval or PRs before and after Code Freeze.

**Pre-requisites**

Reference: SOP - Code Review Process. ***<<Add link of Code Review SOP document after uploading>>***

**Procedure**

Bitbucket repository has monthly dev branches that are created and frozen roughly after 2 sprints. The timelines of code freeze are communicated to the entire GuidingCare Unit working on the monthly release including support and enable teams.

:note:atlassian-note#FFEBE6

Before Code Freeze:

1. The developer creates the feature branch related to the ticket and completes the development activities. Once done, the PR is raised to the relevant Development branch.
2. The PR is then reviewed/approved within the team among Peers and TL.
3. TM then reviews and approves the PR for merge or recommends additional review by DB specialist or Solution Architecture team or any Engineer/Lead that might need to have a look into the PR.
4. Once the necessary PR approvals are in place, TM can merge the PR into the Development branch for Local QA deployment.

After Code Freeze:

1. Post Code Freeze, PRs are generally allowed only for feature defects or Regression defects into the QA branch which is merged with the Dev Branch (after Code Freeze)
2. The above steps are still carried out for the PRs even after Code Freeze.
3. QA Managers are informed and approve the PRs to be merged into the QA branch as necessary.(DevOps ensures that only Product QA Managers have access to merge the PRs and all other Engineering contributors do not have permissions to merge)

### References

Code Review Process - [Code Review & Approval Process - GuidingCare® - Confluence (atlassian.net)](https://healthedge.atlassian.net/wiki/spaces/GC/pages/3077243860/Code+Review+Approval+Process)