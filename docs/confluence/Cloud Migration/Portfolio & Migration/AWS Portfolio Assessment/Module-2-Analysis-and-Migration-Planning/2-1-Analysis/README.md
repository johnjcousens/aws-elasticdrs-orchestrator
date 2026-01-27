# 2-1-Analysis

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867034611/2-1-Analysis

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:49 AM

---

---

title: 2.1 Analysis
-------------------

Goals and Pre-Requisites
------------------------

The primary outcome of Portfolio Analysis is to gain an overall understanding of the customer portfolio of applications, validate assumptions, key dependencies, migration strategies, and plan for the migration. Typically, Portfolio Analysis will come after 

Module 1-Discovery Acceleration and Initial Planning
, although it can also be performed independently whenever data is already available (this can be the case when a Discovery Tool has been deployed or when previous Discovery related engagements have taken place). The main pre-requisite is the availability of 1 full week of programmatic data collection as a minimum (or equivalent data) from all in-scope applications/infrastructure, including network communication data in order to evaluate application dependencies.

The Portfolio Analysis sessions can be conducted as a series of individual working sessions or workshops. Adapt the agenda and delivery format considering the context of your engagement. Plan for as many sessions/workshops as needed. Completing a full portfolio assessment could take several weeks/months, depending the size of the scope.

Primary Outcomes (after conducting all sessions/workshops)
----------------------------------------------------------

1. **Template - Application and Infrastructure Inventory
   -** the finalized Inventory should include:

   1. List of all physical and virtual servers in scope and their attributes
   2. List of all applications and the relevant attributes utilized for prioritization, disposition, categorization, etc.
   3. List of all databases in scope and their attributes
   4. Server to applications mapping
   5. Server to server dependency mapping
   6. Database to server mapping
   7. Database to application mapping
   8. Application to application dependency mapping
   9. Remote storage and its mapping to applications and infrastructure
   10. **A Tested/Iterated

       Artifact - 7R Disposition Tree,**


       Artifact - Application Prioritization Criteria, and 


       2-2 Wave Planning

Portfolio Analysis Workshop(s) Checklist
----------------------------------------



Expectation setting with the customer executive/leader for the events



Review tactical and strategic goals of the event, discuss expected friction points



Establish the logistics to escalate to the customer executive if it is needed



Confirm attendees from the customer who will represent roles and responsibilities listed in attendees (see agenda). These attendees should be a mix of doers and decision makers



Preview expectations with the attending leaders of each domain (security, applications, etc.)



Document assigned roles and expected attendees by session / tracks



Confirm logistics for the meeting (single meeting room for all participants or preferred customer tool for virtual collaboration)

* Confirm infrastructure and application data set is ready for use

Agenda, Sessions, and Participants
----------------------------------

**Note**: repeat these sessions as many times as needed in order to cover the entire scope. Completing a full portfolio assessment could take several weeks/months, depending the size of the scope.

Activity Details
----------------



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th>Activity</th>
<th>Details / Guidance </th>
<th>Artifacts</th>
</tr>
<tr>
<td>Asset &amp; Dependency Output Review</td>
<td>Typically, the output of the discovery tooling or equivalent data (e.g.
                CMDB). Establish clear processes to access the data in a secure manner
                and how it will be updated.</td>
<td>
Discovery Tool of choice or equivalent source of data
</td>
</tr>
<tr>
<td colspan="1">Review, Identify and Validate Application Stacks</td>
<td colspan="1">
Some discovery tools have the ability to auto-generate application stacks
                    (note that this action could have a different name depending the tool),
                    this feature uses internal algorithms to analyze processes and communication
                    data in order to determine (indicatively) which infrastructure components
                    seem to make up a business application. Note that this is not about identifying
                    software running on a server, but rather a business application that is
                    made up of several infrastructure components.
In some cases, the name of the application itself will be suggested, this
                    is typically the case for well-known commercial products. However, for
                    proprietary applications or when there is a specific internal name for
                    a commercial product, these will not be detected. In these cases, the application
                    will appear as either an 'unknown application', 'auto-generated stack',
                    or by some type of definition inherent to the discovery tool. These ‘stacks’
                    must be validated by confirming the infrastructure that has been grouped
                    and by naming them. Likewise, when alternative sources of data are being
                    used, the work should focus on validating the mapping between application
                    and infrastructure, identifying dependencies, and abtaining further application
                    metadata according to
                <ac:link>
<ri:page ri:content-title="Data-Collection-Requirements-(all-stages)" ri:version-at-save="2"></ri:page>
<ac:plain-text-link-body>Data Collection Requirements (all stages)</ac:plain-text-link-body>
</ac:link>

Work with the relevant stakeholders to name/validate the applications
                    and to validate/update the associated infrastructure as needed. Also, collect
                    additional attributes, at a high-level, such as environment, owner, location,
                    criticality, existence of disaster recovery components, and others. In
                    addition, highlight complex applications that might require special treatment
                    and cases where AWS offerings such as SAP, Mainframe, Windows, DB Freedom
                    could apply.
<strong>Important Note 1:</strong>  when discovery tooling is being used,
                    educate the stakeholders that the tool automates the process based on a
                    given logic combining process and communication data. Validating the application
                    discovery performed by the tool is a time consuming and necessary step
                    that requires manual intervention.
Likewise, when using a discovery tool that does not have the capability
                    to auto-generate application stacks, the mapping of application to infrastructure
                    becomes a complete manual activity. The amount of effort required will
                    depend on the information provided by the tool. In these cases, educate
                    the customer on the process of identification in order to establish independent
                    working groups that can perform the required work.
<strong>Important Note 2:</strong> even in the cases where the discovery
                    tooling does automated application to infrastructure mapping, depending
                    on the size of the scope, the time allocated in the workshops might not
                    be sufficient to validate all applications. Ensure the stakeholders are
                    comfortable with completing the remaining applications on subsequent sessions.
                    Alternatively, it is recommended to plan for as many workshops as needed
                    to cover the entire scope.
</td>
<td colspan="1">
Discovery Tool of choice or equivalent source of data
<ac:link>
<ri:page ri:content-title="Template---Application-and-Infrastructure-Inventory" ri:version-at-save="2"></ri:page>
<ac:plain-text-link-body>Template - Application and Infrastructure Inventory </ac:plain-text-link-body>
</ac:link>
<ac:link>
<ri:page ri:content-title="Data-Collection-Requirements-(all-stages)" ri:version-at-save="2"></ri:page>
<ac:plain-text-link-body>Data Collection Requirements (all stages)</ac:plain-text-link-body>
</ac:link>
</td>
</tr>
<tr>
<td colspan="1">7R Disposition Tree </td>
<td colspan="1">
The 7R Disposition Tree is used as a guide for Application Owners and
                    Architects, among others, to evaluate which path to take when migrating
                    an application. Each project will have unique circumstances and decision-making
                    processes that need to be incorporated into the tree logic.
A default 7R disposition tree is included with this guide. Iterate it
                    and test it with sample applications, and introduce as many changes as
                    necessary. In addition, ensure the definition of the 7Rs is agreed among
                    stakeholders. This could include changing those definitions if the stakeholders
                    feel comfortable with an alternate description or naming. For example,
                    some teams prefer to separate between Refactor and Rearchitect whereas,
                    by default, AWS groups both together. Ensure a common language is used
                    across Customer, AWS and Partners.
<strong>Important Note:</strong> the tree will require further reviews
                    and updates based on learning and data gathering to reach a baselined version.
                    It typically takes 2 to 3 weeks to establish a baselined tree.
</td>
<td colspan="1">
<ac:link>
<ri:page ri:content-title="Artifact-7R-Disposition-Tree" ri:version-at-save="1"></ri:page>
<ac:plain-text-link-body>Artifact - 7R Disposition Tree</ac:plain-text-link-body>
</ac:link>
</td>
</tr>
<tr>
<td>
<br/>Application Prioritization Criteria</td>
<td>
Identify key application attributes to determine the order in which applications
                    will be migrated. This is a key input for constructing migration wave plans.
If discovery tooling in use lacks the capability/features to perform prioritization,
                    use the Migration Portfolio Assessment (MPA) (available to AWS Employees
                    and Partners) to perform prioritization. It will be required to export
                    all application and infrastructure data from the discovery tool and import
                    it into MPA. Request permission from the data owner(s) to upload their
                    data into MPA. 
When exporting data from the discovery tool, consider exporting all assets
                    (applications and infrastructure), as well as Communication (or dependency)
                    data. The communications data will be required for Wave Planning with MPA.
                    Once the data has been imported into MPA, navigate to the Plan section,
                    application prioritization.
The objective is to decide, alongside relevant stakeholders, which application
                    attributes will be used to prioritize the order in which applications will
                    be moved to AWS, and then assigning a corresponding weighting to the possible
                    values of those attributes. Next, define the attribute relevance level
                    for prioritization. If MPA is being used, the higher the relevance the
                    higher the importance of that attribute for prioritization. Customers will
                    typically prefer to migrate non-critical applications in the initial waves
                    such as non-production or dev environments. For example, if Development
                    applications from specific business units/departments are good initial
                    candidates, then the environment and business unit attributes will have
                    higher relevance in MPA than other application attributes.
The result will be a ranking of applications. If the weighting/criticality
                    is correct, the top 5 should be good initial candidates for migration.
                    If the top applications do not make sense, adjust the criteria and recreate
                    the list. It typically takes several iterations to reach a baselined version.
</td>
<td>
Discovery Tool of choice or equivalent source of data
<a href="http://mpa-proserve.amazonaws.com/">Link to MPA</a>

<ac:link>
<ri:page ri:content-title="Artifact---Application-Prioritization-Criteria" ri:version-at-save="2"></ri:page>
<ac:plain-text-link-body>Artifact - Application Prioritization Criteria</ac:plain-text-link-body>
</ac:link>
</td>
</tr>
<tr>
<td colspan="1">Identify Pilot Applications (or initial migration candidates)</td>
<td colspan="1">Perform 
                <ac:link>
<ri:page ri:content-title="Detailed-Application-Assessment-(Pilot-apps-or-waves)" ri:version-at-save="1"></ri:page>
<ac:plain-text-link-body>Detailed Application Assessment (Pilot apps or waves)</ac:plain-text-link-body>
</ac:link>
                 in
                order to confirm/validate/update the initial candidates scope.</td>
<td colspan="1">
<ac:link>
<ri:page ri:content-title="Detailed-Application-Assessment-(Pilot-apps-or-waves)" ri:version-at-save="1"></ri:page>
<ac:plain-text-link-body>Detailed Application Assessment (Pilot apps or waves)</ac:plain-text-link-body>
</ac:link>
</td>
</tr>
<tr>
<td colspan="1">Wave Planning</td>
<td colspan="1">
The objective is to leverage the prioritization criteria and create a
                    migration wave plan. Note that Wave Planning can take several weeks of
                    iteration. Start with a first draft and focus on validating the first few
                    Waves, especially Wave 1. 
See linked artifact for further guidance.
</td>
<td colspan="1">
<ac:link>
<ri:page ri:content-title="2-2-Wave-Planning" ri:version-at-save="1"></ri:page>
<ac:plain-text-link-body>2-2 Wave Planning</ac:plain-text-link-body>
</ac:link>
</td>
</tr>
</tbody>
</table>

