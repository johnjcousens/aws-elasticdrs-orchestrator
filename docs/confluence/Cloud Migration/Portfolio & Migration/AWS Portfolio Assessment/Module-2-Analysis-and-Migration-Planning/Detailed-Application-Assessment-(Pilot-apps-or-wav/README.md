# Detailed-Application-Assessment-(Pilot-apps-or-waves)

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867065766/Detailed-Application-Assessment-%28Pilot-apps-or-waves%29

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:50 AM

---

---

Overview
========

At this stage of Portfolio Assessment it is assumed that the activities under [1-Discovery Acceleration and Initial Planning](../Module-1-Discovery-Acceleration-and-Initial-Planning) have been completed or that there is enough data available to work with a subset of applications in order to perform a detailed assessment in readiness to migrate a batch of apps.

Depending on the migration strategy chosen for these applications, there could be a significant variation in the level of detail required. For example, most Rehost strategies will require a simple design and less discovery details, focusing mainly in validating technology stack compatibility, operations, and security. On the other hand, a Refactor approach will require detailed designs and understanding of the application in order to design its future state. Consider adapting the scope of the detailed assessment, questionnaires and design templates to meet the level of complexity required. For efficiency, consider also producing and reusing architectural templates/designs that could apply to more than one application of similar characteristics.

Primary Outcomes
================

1. **AWS Application Architecture Design for each application in a given batch (pilot apps or specific wave)**
2. **Confirmed Migration Strategy for each app**
3. **(Optional) Estimated Run Rate in AWS for each app**

Context
=======

Assist the customer with confirming a subset of applications targeted for migration, performing a detailed discovery, and conducting future state design sessions. The duration of the assessment is dependent on the number of applications to be assessed and its complexity. The base estimate is of 1 to 3 days per application; the recommendations is to work with a maximum of 3 to 5 applications per batch. However, this can change based on planning, application complexity and customer needs.

The primary goals are:

* Identify and confirm a scope of applications (this could include assisting the customer to develop a prioritization criteria to identify those applications). Consider cases where a given architecture and migration strategy can be later re-used by other applications.
* Dive Deep current architecture, functional and non-functional requirements for each application in the current batch
* Create an initial AWS Design for the applications outlining requirements and target architecture, and including an AWS Run Cost estimate
* Identify a suitable migration strategy for each app

Pre-Requisites
==============

* Identify and confirm stakeholders for each application
* Organize a workshop or working session with the relevant stakeholders
* Identify pre-existing sources of data (documentation, diagrams, discovery tooling, inventories, dependency data) and ensure they are available for the assessment
* Review and update the 

  Artifact - 7R Disposition Tree
   to aid the selection of the migration strategy

Workshop Checklist
------------------



Expectation setting with the customer executive/leader for the event



Review tactical and strategic goals of the event, discuss expected friction points



Establish the logistics to escalate to the customer executive if it is needed



Confirm attendees from the customer who will represent roles and responsibilities listed in attendees (see agenda). These attendees should be a mix of doers and decision makers



Preview expectations with the attending leaders of each domain (security, applications, etc.)



Document assigned roles and expected attendees by session / tracks



Confirm logistics for the meeting (single meeting room for all participants or preferred customer tool for virtual collaboration)



Confirm pre-requisites are met

Agenda & Sessions
=================

Application Assessment Workshop Agenda including duration and recommended attendees for each session.

Activity Details
----------------



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th>Day</th>
<th>Session</th>
<th>Details / Guidance </th>
<th>Artifacts / Tools</th>
</tr>
<tr>
<td rowspan="6"><strong>Day 1</strong>
</td>
<td>Goal setting and Business Outcomes</td>
<td>Establish the Goals for the day and review high-level Business drivers
                and customer outcomes (e.g., cost reduction, transformation, etc.)</td>
<td>

<br/>

</td>
</tr>
<tr>
<td>Validate Application Prioritization Criteria (Optional, see Note)</td>
<td>
<strong>Note:</strong> if this party is being performed after 
                <ac:link>
<ri:page ri:content-title="Module-1-Discovery-Acceleration-and-Initial-Planning" ri:version-at-save="2"></ri:page>
<ac:plain-text-link-body>Module 1-Discovery Acceleration and Initial Planning</ac:plain-text-link-body>
</ac:link>
                 the
                    application prioritization criteria is likely to be already established.
                    Use this session to iterate/validate the established criteria if needed.
                    The goal of this session is to establish which key attributes will determine
                    the selection of applications for the detailed assessment. In some cases,
                    it will be known, in advance, which applications are being targeted. In
                    other cases, it will be required to identify the applications.
The objective is to assist the customer to identify key application attributes
                    to determine priority. This includes <span>assigning a corresponding weighting to the possible values of those attributes. Next, define the attribute importance level for prioritization.</span>

The result will be a ranking of applications. If the weighting/criticality
                    is correct, the top 5 should be good initial candidates for assessment.
                    If the top applications do not make sense, adjust the criteria as needed.
</td>
<td>
<ac:link>
<ri:page ri:content-title="Template---Application-and-Infrastructure-Inventory" ri:version-at-save="2"></ri:page>
<ac:plain-text-link-body>Template - Application and Infrastructure Inventory</ac:plain-text-link-body>
</ac:link>
<ac:link>
<ri:page ri:content-title="Artifact---Application-Prioritization-Criteria" ri:version-at-save="2"></ri:page>
<ac:plain-text-link-body>Artifact - Application Prioritization Criteria</ac:plain-text-link-body>
</ac:link>
<a href="https://mpa.accelerate.amazonaws.com/">MPA tool</a> (application
                        prioritization)
</td>
</tr>
<tr>
<td colspan="1">Application Deep Dive</td>
<td colspan="1">
Use the suggested artifacts to conduct a detailed assessment. Ensure the
                    necessary stakeholders to dive deep into the business, architecture, and
                    technology aspects are part of the session.
The use of Discovery Tools for Dependency analysis is highly recommended.
</td>
<td colspan="1">
Discovery Tool of choice
<ac:link>
<ri:page ri:content-title="Artifact---Pilot-Applications" ri:version-at-save="2"></ri:page>
<ac:plain-text-link-body>Artifact - Pilot Applications</ac:plain-text-link-body>
</ac:link>
<ac:link>
<ri:page ri:content-title="Template-Detailed-Application-Discovery-Questionnaire" ri:version-at-save="1"></ri:page>
<ac:plain-text-link-body>Template - Detailed Application Discovery Questionnaire</ac:plain-text-link-body>
</ac:link>
</td>
</tr>
<tr>
<td colspan="1">AWS Application Architecture Design</td>
<td colspan="1">Use the suggested artifacts to create a target design. Consider reusing
                existing architectural patterns if possible.</td>
<td colspan="1">
<ac:link>
<ri:page ri:content-title="Template-Application-AWS-Architecture-Design-and-Migration-Strategy" ri:version-at-save="2"></ri:page>
<ac:plain-text-link-body>Template - Application AWS Architecture Design and Migration Strategy</ac:plain-text-link-body>
</ac:link>
</td>
</tr>
<tr>
<td colspan="1">Migration Strategy and Patterns</td>
<td colspan="1">Use the suggested artifacts to establish a migration strategy and approach,
                including specific technology patterns and migration tooling.</td>
<td colspan="1">
<ac:link>
<ri:page ri:content-title="Template-Application-AWS-Architecture-Design-and-Migration-Strategy" ri:version-at-save="2"></ri:page>
<ac:plain-text-link-body>Template - Application AWS Architecture Design and Migration Strategy</ac:plain-text-link-body>
</ac:link>
<ac:link>
<ri:page ri:content-title="Artifact-7R-Disposition-Tree" ri:version-at-save="1"></ri:page>
<ac:plain-text-link-body>Artifact - 7R Disposition Tree</ac:plain-text-link-body>
</ac:link>
</td>
</tr>
<tr>
<td colspan="1">Wrap-up</td>
<td colspan="1">Review outcomes of the day and next steps</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td><strong>Day 2</strong>
</td>
<td colspan="1">As needed</td>
<td colspan="1">Repeat Deep Dive, AWS Design, and Migration Strategy sessions as needed,
                depending the number of apps in scope</td>
<td colspan="1">
<br/>
</td>
</tr>
<tr>
<td colspan="1"><strong>Day 3</strong>
</td>
<td colspan="1">As needed</td>
<td colspan="1">Repeat Deep Dive, AWS Design, and Migration Strategy sessions as needed,
                depending the number of apps in scope</td>
<td colspan="1">
<br/>
</td>
</tr>
</tbody>
</table>



**Attachments:**