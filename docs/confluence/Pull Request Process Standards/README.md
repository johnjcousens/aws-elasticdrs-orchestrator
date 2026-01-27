# Pull Request Process Standards

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/PLAT/pages/4920606945/Pull%20Request%20Process%20Standards

**Created by:** Michael Pellegrini on July 09, 2025  
**Last modified by:** Michael Pellegrini on July 09, 2025 at 04:49 PM

---

This document defines our shared expectations for opening, reviewing, and merging pull requests. Its goals are to:

* Improve code quality
* Foster consistency across our engineering team
* Increase visibility of changes
* Streamline onboarding
* Encourage respectful, traceable collaboration

Branching Conventions
=====================

Use consistent and descriptive branch names to clearly communicate the purpose of the work.

Name Format
-----------

`<ticket-id>-<short-description>`

### Examples

* `PUX-1234-user-auth`
* `PUX-4567-login-crash`
* `PUX-6789-eslint-upgrade`Target Branch

All pull requests should be opened against the `main` branch, unless specified otherwise.

### Guidelines

* Do not open PRs against other branches unless explicitly requested for a special case.
* The `main` branch should always represent the latest production-ready state of the codebase.
* CI/CD should enforce passing builds on all branches before merging, and on `main` after merging.
* For large features requiring multiple PRs, use PR stacking (sequential PRs where each builds on the previous) rather than long-lived feature branches.
* If a feature branch is absolutely necessary, it should be short-lived (< 2 weeks), regularly rebased against main, and have a clear merge timeline communicated to the team.

PR Titles and Descriptions
==========================

Title Format
------------

PUX-XXX [Type] (section) - [Short summary]

### Example

PUX-423 feature (Setup) Create Line Of Business Groups Search Page

Description Template
--------------------

Encourage or enforce use of a PR template with the following markdown structure:


```
## Summary 
This PR implements [PUX-### Ticket Title](link to jira) by: 
 - Brief description of key changes 
 - Why these changes were made 
 - Any important context or decisions 
 
## Demo/Screenshots 
*Screenshots, videos, or other visual documentation of your feature* 
 
## Reviewer Validation 
**Feature:** [Brief feature description] 
**Scenario:** [Test scenario description] 
**Given:** [Initial conditions] 
**When:** [Action taken] 
**Then:** [Expected outcome] 

Link to existing TestRail scenarios when applicable, or refer to futuer scenarios in TestRail.
 
## PR Author Checks 
[ ] Tests run and pass locally 
[ ] CI/CD passes 
[ ] Branch is up-to-date with main 
[ ] Copilot and human reviews completed 
[ ] No unresolved comments 
[ ] Tests added (if applicable) 
[ ] Documentation updated (if applicable) 
```


### Description Example


```
## Summary 
This PR implements [PUX-1847 Add claim status filtering to dashboard](https://healthedge.atlassian.net/browse/PUX-1847) by: 
 - Adding a multi-select dropdown filter for claim status (Pending, Approved, Denied, Under Review) 
 - Implementing backend API endpoint `/api/claims/filter` to support status-based filtering 
 - Updating the claims table to refresh data when filters are applied 
 - Adding URL state management so filter selections persist on page refresh 

This addresses user feedback that the claims dashboard was difficult to navigate with large volumes of mixed-status claims. 
 
## Demo/Screenshots 
![Filter dropdown demo](screenshot1.png) 
*Shows the new status filter in action - selecting "Pending" and "Under Review" filters the table to show only those claim types* 
 
![Before and after comparison](screenshot2.png) 
*Left: Original dashboard with all claims. Right: Filtered view showing only pending claims* 
 
## Reviewer Validation 
**Feature:** Claim status filtering on dashboard 
**Scenario:** User wants to view only pending claims 
**Given:** User is on the claims dashboard with mixed-status claims visible 
**When:** User selects “Pending” from the status filter drop-down 
**Then:** Table refreshes to show only pending claims, URL updates to reflect filter state 
**Scenario:** Filter state persistence 
**Given:** User has applied status filters 
**When:** User refreshes the page or navigates away and back 
**Then:** Previously selected filters remain active and claims remain filtered 

## PR Author Checks 
[x] Tests run and pass locally 
[x] CI/CD passes 
[x] Branch is up-to-date with main 
[x] Copilot and human reviews completed 
[ ] No unresolved comments 
[x] Tests added (unit tests for filter API, integration tests for UI behavior) 
[x] Documentation updated (API docs updated with new endpoint details) 
```


Review and Approval Process
===========================

PR Author Expectations
----------------------

* Open Draft PRs early - As soon as you have a single commit, open a draft PR for team visibility and early feedback. You can refine the description and details later.
* Keep your branch current - Ensure your branch is up-to-date with main before requesting review and before merging.
* Address failing checks - You're responsible for resolving any failing CI/CD checks, tests, or other automated validations.
* Respond to all feedback - Every review comment must be addressed (see Commenting Guidelines below).

Copilot Review
--------------

* Each PR receives a preliminary review by GitHub Copilot.
* Copilot may identify bugs, logical flaws, or missing best practices.
* These suggestions are helpful but **not authoritative**.
* Human reviewers must still perform a full review before a PR can be merged.

Human Review Requirements
-------------------------

* Standard approval: At least one approval from a senior engineer, lead engineer, SME (subject matter expert), or engineering manager.
* Alternative approval: Two approvals from team members (any level) may substitute for senior approval in most cases.
* Human reviewers should validate comments by CoPilot to ensure they were addressed accurately and accordingly.
* Reviews from multiple team members are encouraged and appreciated.

Commenting Guidelines
---------------------

* **Do not delete comments**. Every comment must be addressed with one of the following:

  + A code change and resolution (you may resolve directly if the fix is clear)
  + A reply explaining why no code change was made, then resolution (Ex: "Chose not to change this because the current approach aligns with our internal standard for XYZ.")
* **Nits:** For minor comments, use the following format:

  + [nit] Rename variable for clarity
  + nit – Rename variable for clarity
  + Reviewer should indicate whether the change should be made in the current PR, or in a future PR.

All comments, including nits, must be resolved - not just replied to. If your response is simply "fixed," you may resolve the comment directly.

PR Size and Commit Practices
============================

Realistic Expectations for PR Size
----------------------------------

We recognize that in this codebase, many PRs will be large by necessity, especially when:

* Adding new page types, which requires updates to a fixed set of system files
* Importing or updating extensive mock data
* Implementing architectural patterns that touch many components

Therefore:

* There is no strict line/size limit, but PRs should still aim to be *as focused and well-structured as possible*.
* If a PR contains many lines for mock data or boilerplate, call this out in the description.

Managing Very Large Features with PR Stacking
---------------------------------------------

For large features that couldn't be broken down during the ticketing process, consider using PR stacking to make the work more reviewable.

### Example stacking approach:

* PR 1: Add fixtures and mock data
* PR 2: Build main functionality (builds on PR 1)
* PR 3: Add comprehensive tests (builds on PR 2)

### PR Stacking Guidelines

* Each PR in the stack should be independently reviewable and represent a logical unit of work.
* Clearly indicate in each PR description which PR it builds upon.
* Consider using branch naming like 1234-feature-01-fixtures, 1234-feature-02-functionality, 1234-feature-03-tests.
* The first PR should include a high-level summary of the entire feature plan.

### When to use PR Stacking

* Review complexity would benefit from logical separation.
* Team capacity allows for sequential review and merging.
* Large amount of expected feature work spanning multiple concerns.

This approach maintains code quality and reviewer sanity while acknowledging the realities of complex feature development.

Commit Strategy
---------------

* **Commit frequently** - Make commits as often as helpful for your development process.
* **Commit messages can be informal** - Within a PR, messages like "fix typo," "woops," "maybe now docker will love me?" or "tests" are perfectly acceptable.
* **Focus on PR title format** - Since we squash and merge PRs into a single commit, ensure your PR title follows our naming conventions rather than worrying about individual commit message formatting.
* **Group commits logically when helpful** - While not required, organizing related changes into logical commits can still be useful for your own development workflow and review process.

**Key point:** Individual commit messages within a PR are for your development convenience. The PR title becomes the final commit message in main, so that's where formatting standards matter most.

PR Review Tips for Large Changes
--------------------------------

For reviewers:

* Focus on business logic, interfaces, and architectural decisions.
* Trust that mock data and boilerplate follow expected formats unless something looks off.

  + Ensure mock data provides a large enough sample size to validate the feature.
* Use GitHub's "Hide whitespace changes" and file filtering features to focus reviews.
* Complete any reviewer validation steps listed in the PR description. These provide structured testing scenarios to verify the feature works as expected.

For authors:

* Use PR descriptions to guide reviewers:

  + "The core logic is in src/utils/transformer.ts"
  + “UserProfile.tsx contains complex changes”
  + "The bulk of this PR is mock data imports - main changes are in components/UserProfile.tsx"
* Include clear reviewer validation steps that allow reviewers to manually test the key functionality and edge cases.

Post-Merge Communications
=========================

Automated Notifications
-----------------------

To ensure visibility and improve ability to search for changes:

* After a PR merges to the `main` branch, the CI pipeline should trigger a **Teams message** in a team-specific PR channel.

* This message should contain the PR’s title, author, and link.