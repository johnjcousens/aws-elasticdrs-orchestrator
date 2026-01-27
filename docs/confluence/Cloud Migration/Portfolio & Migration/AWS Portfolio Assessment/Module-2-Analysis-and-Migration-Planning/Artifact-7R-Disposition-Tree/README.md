# Artifact-7R-Disposition-Tree

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867034671/Artifact-7R-Disposition-Tree

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:50 AM

---

---

title: Artifact 7R Disposition Tree
-----------------------------------

Disposition Tree
================

The following tree is a base model intended to be updated/validated with the relevant stakeholders according to the organization's unique journey and circumstances. It can be edited with [draw.io](https://app.diagrams.net/).

**Important Note:** consider an approach where groups of applications, based on similar architecture, business criticality, and technology stacks are passed through the tree in order to obtain a recommended strategy for the group. This will save time when working with large portfolios.

Migration Strategies
====================



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th class="highlight-blue" width="99">
<strong>Migration</strong> <strong>Strategy</strong>

</th>
<th class="highlight-blue" colspan="1" width="452">Description</th>
<th class="highlight-blue" width="452">
<strong>Sample use cases</strong>

</th>
</tr>
<tr>
<th width="99">
<strong>Retire</strong>

</th>
<td colspan="1" width="452">
<span>Decommission the application without migrating or modernizing</span>

</td>
<td width="452">
<ul>
<li>Application and host decommission at source</li>
<li>No migration to target</li>
<li>Existing Decommission Program Scope</li>
<li>Disaster Recovery Component or Passive instances being recreated in Cloud</li>
</ul>
</td>
</tr>
<tr>
<th width="99">
<strong>Retain</strong>

</th>
<td colspan="1" width="452"><span>Do nothing and keep running the application in the current location</span>
</td>
<td width="452">
<ul>
<li>Client will keep host / application in their source environment</li>
<li>Unknown application, high risk migration</li>
<li>Hard dependency to another application being retained</li>
<li>Unresolved Physical Dependencies</li>
</ul>
</td>
</tr>
<tr>
<th colspan="1" width="99">Relocate</th>
<td colspan="1" width="452">Rapid migration of servers and applications to VMware cloud on AWS</td>
<td colspan="1" width="452">
<ul>
<li>Lift-Shift infrastructure onto AWS at the Hypervisor level</li>
<li>No change in operating model/operations</li>
<li>Very fast migration</li>
</ul>
</td>
</tr>
<tr>
<th width="99">
<strong>Rehost</strong>

</th>
<td colspan="1" width="452">
<span>Rapid migration of servers and applications without architectural, technology or functionality changes</span>


<br/>

</td>
<td width="452">
<ul>
<li>Like for Like application migration of supported workloads to target cloud</li>
<li>Minimal effort to make the application work on the target cloud infrastructure
                        (minimal application layout change)</li>
</ul>
</td>
</tr>
<tr>
<th width="99">
<strong>Repurchase</strong>

</th>
<td colspan="1" width="452">Purchase, configure or customize a COTS (Commercial Of The Shelf) or SaaS
                (Software as a Service) product</td>
<td width="452">
<ul>
<li>Application will be replaced, potentially to new cloud-native application
                        or SaaS platform. Data migration may be needed.</li>
</ul>
</td>
</tr>
<tr>
<th width="99">
<strong>Replatform</strong>

</th>
<td colspan="1" width="452">Enhanced modernization or upgrade of the application/service underlaying
                components such as OS and Databases</td>
<td width="452">
<ul>
<li>Up-Version of the OS and/or Database onto the target cloud</li>
<li>Data migration to cloud storage service</li>
<li>Application reinstallation on the target</li>
<li>DB migration onto RDS (same product)</li>
</ul>
</td>
</tr>
<tr>
<th width="99">
<strong>Refactor</strong> <strong>/</strong>  <strong>Rearchitect</strong>

</th>
<td colspan="1" width="452"><span>Modernization of the application by applying changes to the code base in order to support a modernization pattern and/or changing its architecture (e.g., containerization, serverless)</span>
</td>
<td width="452">
<ul>
<li>OS and/or Database porting</li>
<li>Middleware and application change to cloud service offering</li>
<li>Data conversion; Database transition to MySQL, Aurora, etc.</li>
<li>Application architecture changes may also require Up-Version or Porting</li>
<li>Custom / complex application changes</li>
</ul>
</td>
</tr>
</tbody>
</table>



7R's Workshop - Deck
====================

**Attachments:**

[7Rs-DecisionTree-baseModel.drawio.png](../../attachments/7Rs-DecisionTree-baseModel.drawio.png)