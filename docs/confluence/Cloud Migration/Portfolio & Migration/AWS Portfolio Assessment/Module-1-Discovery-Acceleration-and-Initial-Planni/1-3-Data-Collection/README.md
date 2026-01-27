# 1-3-Data-Collection

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867001523/1-3-Data-Collection

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:53 AM

---

---

title: 1.3 Data Collection
--------------------------

Overview
========

Data collection is the process of gathering metadata from applications and infrastructure. The process is iterative throughout all stages of assessment where data quantity and fidelity will increase as progress is made. At this stage, the focus is on gathering general data that can help to establish an initial inventory leading to the creation of a directional business case and the identification of initial migration candidates. The objective of this group of activities is to complete the data collection roll-out (i.e., discovery tool collecting data from all targeted systems) and monitor its progress, collect manual information from infrastructure assets that cannot be targeted by the discovery tool (e.g., legacy systems, secure zones), and to collect application metadata.

Pre-requisites Checklist
------------------------



Discovery Tool installed and configured (or alternative sources identified and validated)

* Data Collection roll-out plan defined (including agent roll-out when needed) - Stakeholders for application metadata identified

Activity List
=============



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th>Activity</th>
<th>Details / Guidance</th>
<th>Artifacts and Resources</th>
</tr>
<tr>
<td>Monitor programmatic data collection</td>
<td>Ensure data collection is progressing and that any issues are being actively
                addressed. Assist the customer with obtaining support from the tooling
                vendor if required.</td>
<td>
Discovery Tool of choice
</td>
</tr>
<tr>
<td>Manual Infrastructure discovery</td>
<td>
In most environments there will be cases where the discovery tool of choice
                    does not support a given legacy system. For example, old operating system
                    versions, legacy platforms such as AS400 or Mainframe, etc. If these systems
                    are in-scope for migration, recommend and perform manual discovery. This
                    could require connecting to those systems directly, or the use of scripts
                    that can be obtained from the discovery tooling vendor, platform teams
                    or by specialized AWS practices. Conduct manual discovery workshops if/when
                    necessary.
</td>
<td>
<ac:link>
<ri:page ri:content-title="Template---Application-and-Infrastructure-Inventory" ri:version-at-save="1"></ri:page>
<ac:plain-text-link-body>Template - Application and Infrastructure Inventory</ac:plain-text-link-body>
</ac:link>
</td>
</tr>
<tr>
<td colspan="1">Application Metadata</td>
<td colspan="1">
Work with the relevant teams to identify key application attributes such
                    as application names, mapped infrastructure, environments, criticality,
                    complexity, and others. Use the ongoing output of the discovery tool where
                    possible in order to label auto-discovered applications.
Leverage <span>Migration Portfolio Assessment (MPA) tool (available to AWS Employees and Partners)</span> functionality
                    to send customized online questionnaires to ingest application data whenever
                    possible.
</td>
<td colspan="1">
<ac:link>
<ri:page ri:content-title="Data-Collection-Requirements-(all-stages)" ri:version-at-save="2"></ri:page>
<ac:plain-text-link-body>Data Collection Requirements (all stages)</ac:plain-text-link-body>
</ac:link>
<ac:link>
<ri:page ri:content-title="Template---Application-and-Infrastructure-Inventory" ri:version-at-save="1"></ri:page>
<ac:plain-text-link-body>Template - Application and Infrastructure Inventory</ac:plain-text-link-body>
</ac:link>
<a href="http://mpa-proserve.amazonaws.com/">MPA tool</a>

</td>
</tr>
</tbody>
</table>



Primary Outcomes
================

1. **Data Collected and available on a defined data repository**