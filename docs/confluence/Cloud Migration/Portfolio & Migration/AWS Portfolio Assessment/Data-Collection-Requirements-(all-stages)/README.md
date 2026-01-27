# Data-Collection-Requirements-(all-stages)

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867034586/Data-Collection-Requirements-%28all-stages%29

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:49 AM

---

---

title: Data Collection Requirements (All Stages)
------------------------------------------------

Introduction
============

Portfolio Assessment Data Requirements vary depending the offering module. The following table specifies the typical attributes required. Use this table for socializing data requirements and update it based on the project circumstances. Combine with the

Artifact - Data Sources and Tooling Assessment
in order to match data fidelity level to data source and perform a gap analysis.

Business Drivers, Outcomes, and Goals are not specified in the data requirements below. However, these are considered mandatory input across all stages and activities. See 

Artifact - Business Drivers and Technical Guiding Principles

Data Requirements per Module
============================

**Reference:**

**Module 1:**


Module 1-Discovery Acceleration and Initial Planning
 (DAP)

**Module 2 (detailed apps assessment):**


Detailed Application Assessment (Pilot apps or waves)

**Module 2 (portfolio level information):**


Module 2-Portfolio Analysis and Migration Planning

**Module 3:**


Module 3-Continuous Application Assessment
 (Wave assessment)

**R = Required | O = Optional**



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th colspan="1">Data Category</th>
<th>Attribute Name</th>
<th>Description</th>
<th colspan="1">
Module 1
DAP
</th>
<th colspan="1">
Module 2
(detailed apps assessment)
</th>
<th colspan="1">
Module 2
(portfolio level information)
</th>
<th colspan="1">
Module 3
(Wave assessment)
</th>
<th colspan="1">Directional Business Case</th>
<th colspan="1">Gap Analysis</th>
</tr>
<tr>
<td rowspan="45"><strong>Application</strong>
</td>
<td>Application ID</td>
<td>A unique ID. Typically available on existent CMDBs or other internal inventories
                and control systems. Consider creating unique IDs whenever these are not
                defined.</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1"><span><em>35 of applications missing ID</em></span>
</td>
</tr>
<tr>
<td>Application Name</td>
<td>Application name. Including COTS vendor and product name when applicable.</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Description</td>
<td colspan="1">Primary application function and context</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Environment Type</td>
<td colspan="1">E.g., production, pre-production, development, test, sandbox</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Migration Wave</td>
<td colspan="1">ID or Name of the migration wave for this application</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Business Unit</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Business Owner</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Criticality</td>
<td colspan="1">High/Medium/Low E.g., strategic or revenue generating application, supporting
                a critical function, etc.</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Application Type</td>
<td colspan="1">E.g., web application, database, technical application, shared service</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Recovery Time Objective (RTO)</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Recovery Point Objective (RPO)</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Availability</td>
<td colspan="1">E.g., 365/24/7</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Service Level Agreement (SLA)</td>
<td colspan="1">E.g., 99.8%</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Revenue Generating/Strategic (Y/N)</td>
<td colspan="1">E.g., Directly or indirectly influences company revenue</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Location</td>
<td colspan="1">E.g., DC1 New York</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Users Location</td>
<td colspan="1">E.g., US </td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Number of Users (concurrent)</td>
<td colspan="1">E.g., 250</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Release Cycle</td>
<td colspan="1">E.g., Monthly</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Next Release Date</td>
<td colspan="1">Specific date</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Maintenance Cycle</td>
<td colspan="1">E.g., Monthly</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Maintenance Window</td>
<td colspan="1">E.g., Saturdays 10pm to Sunday 12pm EST</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Migration Strategy</td>
<td colspan="1">One of the AWS 7R's</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Migration Considerations</td>
<td colspan="1">Any relevant information for migration</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Dependencies</td>
<td colspan="1">Upstream/downstream dependencies to internal/external applications or
                services</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Application Tiers</td>
<td colspan="1">E.g., 3 (front-end, application, database)</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Architecture Type</td>
<td colspan="1">E.g., SOA, Monolith</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Application Support Team</td>
<td colspan="1">Primary support team for this application</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Change Control Procedures</td>
<td colspan="1">Change control process</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Licensing Requirements</td>
<td colspan="1">Commodity software license type (e.g., Ms SQL Server Enterprise)</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">is COTS (Y/N)</td>
<td colspan="1">Commercial Of The Shelf software or internal development</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">COST Vendor</td>
<td colspan="1">E.g., IBM</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>COTS Product/Version</td>
<td>COTS Product and Version</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>Compliance Framework</td>
<td>Frameworks applicable to the workload (e.g., HIPPA, SOX, PCI-DSS, ISO,
                SOC, FedRAMP)</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>Regulatory Requirements</td>
<td>List of any regulations applicable to this workload</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>Data Sovereignty Requirements</td>
<td>
<br/>
</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>Data Classification</td>
<td>PII, Public, etc</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Monitoring Solution</td>
<td colspan="1">How is this application monitored? specify products</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Disaster Recovery (Y/N)</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Disaster Recovery Plan</td>
<td colspan="1">Links to existing DR Plans location</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>Software Licence Cost</td>
<td>Costs for software license</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Software Operations Cost</td>
<td colspan="1">Cost of normal operations</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Software Maintenance Cost</td>
<td colspan="1">Cost of scheduled maintenance</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Target AWS Region(s)</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Target AWS Account(s) #</td>
<td colspan="1">
<br/>
</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Target AWS Service(s)</td>
<td colspan="1">E.g., EC2, EKS, ECS, etc.</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td class="highlight-grey" colspan="1"><strong>Data Category</strong>
</td>
<td class="highlight-grey" colspan="1"><strong>Attribute Name</strong>
</td>
<td class="highlight-grey" colspan="1"><strong>Description</strong>
</td>
<td class="highlight-grey" colspan="1">
<strong>Module 1</strong>

<strong>DAP</strong>

</td>
<td class="highlight-grey" colspan="1">
<strong>Module 2</strong>

<strong>(detailed apps assessment)</strong>

</td>
<td class="highlight-grey" colspan="1">
<strong>Module 2</strong>

<strong>(portfolio level information)</strong>

</td>
<td class="highlight-grey" colspan="1">
<strong>Module 3</strong>

<strong>(Wave assessment)</strong>

</td>
<td class="highlight-grey" colspan="1"><strong>Directional Business Case</strong>
</td>
<td class="highlight-grey" colspan="1"><strong>Gap Analysis</strong>
</td>
</tr>
<tr>
<td rowspan="40"><strong>Infrastructure</strong>
</td>
<td>Unique Identifier</td>
<td>E.g., Asset ID. Typically available on existent CMDBs or other internal
                inventories and control systems. Consider creating unique IDs whenever
                these are not defined.</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>Asset Name</td>
<td>E.g., VM name, CMDB record name</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Asset Type</td>
<td colspan="1">E.g., Physical server, virtual server, container, virtual appliance, physical
                appliance, physical device, etc.</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Hostname</td>
<td colspan="1">Network name</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>DNS Name (FQDN)</td>
<td>Fully Qualified Domain Name</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>Location</td>
<td>E.g., DC 1 - New York</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Description</td>
<td colspan="1">Primary role/function</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Environment Type</td>
<td colspan="1">E.g., production, pre-production, development, test, sandbox</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">IP Address(es)</td>
<td colspan="1">IP Address, preferably in &lt;IP-Address&gt;/&lt;Netmask&gt; format</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Operating System</td>
<td colspan="1">E.g., Windows Server</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Operating System Major Version</td>
<td colspan="1">E.g., 2016</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Licensing Requirements</td>
<td colspan="1">Commodity license type (e.g., RHEL Standard)</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Hypervisor</td>
<td colspan="1">When applicable, e.g., vmware</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">State</td>
<td colspan="1">E.g., powered on, active, inactive, powered off</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Number of CPUs</td>
<td colspan="1">Physical of virtual processors</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>Number of CPU Cores</td>
<td>Cores per processor</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td>Number of CPU Threads</td>
<td>Threads per core</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Total Memory</td>
<td colspan="1">Total allocated memory</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Attached/Local Storage Total Size</td>
<td colspan="1">Total allocated storage space from local or attached volumes</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Attached/Local Storage Total Used Size</td>
<td colspan="1">Total used storage space from local or attached volumes</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Remote Storage</td>
<td colspan="1">E.g., NAS volumes</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Peak CPU Usage (%)</td>
<td colspan="1">Max usage over a period of time (typically 30 days)</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Average CPU Usage (%)</td>
<td colspan="1">Average usage over a period of time (typically 30 days)</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Peak Memory Usage</td>
<td colspan="1">Max usage over a period of time (typically 30 days)</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Average Memory Usage</td>
<td colspan="1">Average usage over a period of time (typically 30 days)</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Attached/Local Storage Max IOPS</td>
<td colspan="1">Average usage over a period of time (typically 30 days)</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Attached/Local Storage Average IOPS</td>
<td colspan="1">Average usage over a period of time (typically 30 days)</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Network Max Read/Write</td>
<td colspan="1">Max usage over a period of time (typically 30 days)</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Network Average Read/Write</td>
<td colspan="1">Average usage over a period of time (typically 30 days)</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">is Shared Infrastructure (Y/N)</td>
<td colspan="1">Yes or No to denote infrastructure services that provide shared services
                such as authentication provider, monitoring systems, backup services, and
                similar services</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Application Mapping </td>
<td colspan="1">Applications or application components that run in this infrastructure</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Communication Data</td>
<td colspan="1">E.g., server to server</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Cost</td>
<td colspan="1">Fully loaded costs for bare-metal servers including H/W, maintenance,
                operations, storage (SAN, NAS, Object), O/S license, share of rackspace,
                data center overheads,</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">AWS Target Region</td>
<td colspan="1">Destination Region</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">AWS Target Account #</td>
<td colspan="1">Destination Account</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">AWS Target Service</td>
<td colspan="1">E.g., EC2, EKS</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">AWS Target Subnet</td>
<td colspan="1">Subnet name</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">AWS Target Instance Type</td>
<td colspan="1">Instance type, e.g., m5.xlarge</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">AWS Target Security Group(s)</td>
<td colspan="1">Security Group(s) name(s)</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">AWS Target Other</td>
<td colspan="1">Other relevant target information as needed (e.g., IAM roles)</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td class="highlight-grey" colspan="1"><strong>Data Category</strong>
</td>
<td class="highlight-grey" colspan="1"><strong>Attribute Name</strong>
</td>
<td class="highlight-grey" colspan="1"><strong>Description</strong>
</td>
<td class="highlight-grey" colspan="1">
<strong>Module 1</strong>

<strong>DAP</strong>

</td>
<td class="highlight-grey" colspan="1">
<strong>Module 2</strong>

<strong>(detailed apps assessment)</strong>

</td>
<td class="highlight-grey" colspan="1">
<strong>Module 2</strong>

<strong>(portfolio level information)</strong>

</td>
<td class="highlight-grey" colspan="1">
<strong>Module 3</strong>

<strong>(Wave assessment)</strong>

</td>
<td class="highlight-grey" colspan="1"><strong>Directional Business Case</strong>
</td>
<td class="highlight-grey" colspan="1"><strong>Gap Analysis</strong>
</td>
</tr>
<tr>
<td rowspan="16"><strong>Databases</strong>
</td>
<td colspan="1">Infrastructure</td>
<td colspan="1">Relevant attributes as per Infrastructure section</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Primary Usage Type</td>
<td colspan="1">E.g., OLTP, OLAP, Other</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Source Engine Type</td>
<td colspan="1">E.g., Oracle</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Source Engine Version</td>
<td colspan="1">E.g., 19.0.0.0</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Licensing Model</td>
<td colspan="1">E.g., Enterprise</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Database Size</td>
<td colspan="1">Size of Database</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Schemas</td>
<td colspan="1">Number of schemas</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Throughput</td>
<td colspan="1">Database instance throughput, typically in MBps</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Replication Enabled (Y/N)</td>
<td colspan="1">Indicate existence of replicas</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Table Partitioning (Y/N)</td>
<td colspan="1">Indicate table partitioning</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Encryption (Y/N)</td>
<td colspan="1">Indicate current data encryption</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Connection Pool</td>
<td colspan="1">Indicates connection pool</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Database Extensions</td>
<td colspan="1">Indicates use of database extensions</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">SSL Support (Y/N)</td>
<td colspan="1">Indicate use of SSL</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">AWS Target DB Engine</td>
<td colspan="1">E.g. Oracle</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">AWS Target Other</td>
<td colspan="1">Other relevant target information as needed</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td class="highlight-grey" colspan="1"><strong>Data Category</strong>
</td>
<td class="highlight-grey" colspan="1"><strong>Attribute Name</strong>
</td>
<td class="highlight-grey" colspan="1"><strong>Description</strong>
</td>
<td class="highlight-grey" colspan="1">
<strong>Module 1</strong>

<strong>DAP</strong>

</td>
<td class="highlight-grey" colspan="1">
<strong>Module 2</strong>

<strong>(detailed apps assessment)</strong>

</td>
<td class="highlight-grey" colspan="1">
<strong>Module 2</strong>

<strong>(portfolio level information)</strong>

</td>
<td class="highlight-grey" colspan="1">
<strong>Module 3</strong>

<strong>(Wave assessment)</strong>

</td>
<td class="highlight-grey" colspan="1"><strong>Directional Business Case</strong>
</td>
<td class="highlight-grey" colspan="1"><strong>Gap Analysis</strong>
</td>
</tr>
<tr>
<td rowspan="8"><strong>Storage</strong>
</td>
<td colspan="1">Infrastructure</td>
<td colspan="1">Relevant attributes as per Infrastructure section</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Storage Type</td>
<td colspan="1">E.g., NAS, Object Storage</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Disks Type</td>
<td colspan="1">E.g., HDD, SSD</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Block Size (KB)</td>
<td colspan="1">E.g., 4KB</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Throughput (MBps)</td>
<td colspan="1">Total throughput</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Replication Enabled (Y/N)</td>
<td colspan="1">Indicates volume being replicated</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Encryption Enabled (Y/N)</td>
<td colspan="1">Indicates encryption enabled</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Snapshots (Y/N)</td>
<td colspan="1">Indicate existence of regular snapshots</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<th colspan="1"><strong>Data Category</strong>
</th>
<th colspan="1"><strong>Attribute Name</strong>
</th>
<th colspan="1"><strong>Module 1</strong>
</th>
<th colspan="1">
<strong>Module 1</strong>

<strong>DAP</strong>

</th>
<th colspan="1">
<strong>Module 2</strong>

(detailed apps assessment)
</th>
<th colspan="1">
<strong>Module 2</strong>

(portfolio level information)
</th>
<th colspan="1">
<strong>Module 3</strong>

(Wave assessment)
</th>
<th colspan="1"><strong>Directional Business Case</strong>
</th>
<th colspan="1"><strong>Gap Analysis</strong>
</th>
</tr>
<tr>
<td rowspan="4"><strong>Networks</strong>
</td>
<td colspan="1">Size of pipe (Mb/s), Redundancy (Y/N)</td>
<td colspan="1">Current WAN link(s) specifications (e.g., 1000 Mb/s redundant)</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Link Utilization</td>
<td colspan="1">Peak and Average utilization, egress data transfer (GB/month)</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Latency (ms)</td>
<td colspan="1">Current latency between locations</td>
<td colspan="1">O</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">R</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1">Cost</td>
<td colspan="1">Current cost per month</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">O</td>
<td colspan="1">
<br/>
</td>
</tr>
</tbody>
</table>

