# AWS Portfolio Assessment

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867034518/AWS%20Portfolio%20Assessment

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 03:02 AM

---

Introduction
============

**Application Portfolio Assessment for AWS Cloud Migration** is a modular offering covering all phases of the AWS Migration Framework (Assess, Mobilize, and Migrate & Modernize). It goals to discover, analyze, and plan for a portfolio of applications and associated infrastructure moving to AWS. The offering is delivered as a several sprint engagement, depending the selected modules. Throughout the modules, application and infrastructure metadata are gathered and compiled in an iterative manner in order to create deliverables and accelerate time to migration.

Depending the type of engagement and desired outcomes you may not perform all modules. However, modules 2 and 3 rely on outcomes of previous modules. In all cases, verify that the module pre-requisites are met.

![JourneyTimeline.png](images/JourneyTimeline.png)

**Discovery Module**: ***\*D****iscovery Acceleration and initial Planning***\*(DAP),** for identifying existing data sources, required information, assessing, installing, and running discovery tooling, identifying the scope, building a preliminary inventory of applications and associated infrastructure (compute, storage, networks), initial criteria for prioritization, initial migration strategy disposition, identifying candidates for pilot applications (or wave 1), and producing a directional business case (via [Migration Evaluator](https://aws.amazon.com/migration-evaluator/)).

**Analysis Module**: ***\*[Module 2-Portfolio Analysis and Migration Planning](DK-Assessment/Module-2-Analysis-and-Migration-Planning),***\* sprint based iteration to baseline a complete application/infrastructure inventory, understand key migration pre-requisites and dependencies, baseline the prioritization criteria and migration strategy disposition, and produce a high-confidence migration wave plan. This module also includes a detailed assessment (current and future architecture) for the Pilot Applications (or Wave 1).

**Wave Assessment Module**: **[Module 3-Continuous Application Assessment](DK-Assessment/Module-3-Continuous-Application-Assessment/),** a sequence of detailed application assessment per targeted wave, including the iteration of the migration wave plans produced in the previous module.

### Portfolio level assessment (entire scope) vs detailed application assessment (pilot apps, waves)

**Application Portfolio Assessment** is performed at two levels: 
**1/ Portfolio Level** is about collecting and analyzing general data about applications and infrastructure in order to obtain a high-level view of the entire portfolio, including technical and business aspects. This is key in order to understand priorities, the scope of the program, and to create high-confidence plans. **2/ Application Level** is about diving deep into the architecture/technology, AWS design, and migration strategy of the in-scope applications in order to perform the migration. Application Level detailed discovery is typically time consuming and it is normally done in a sequence of smaller chunks, aligned to migration waves, throughout the project lifecycle.The output of the Portfolio and Application level discovery will be a direct input to the Platform and Migration workstreams to perform the migrations.

Overall objectives and outcomes
===============================

* Discovery Acceleration and initial Planning
  + Implemented automated discovery tooling
  + Initial application/infrastructure inventory
  + Initial 7R disposition for infrastructure
  + Application prioritization criteria
  + Identified prioritized applications
  + Initial migration plan for prioritized applications
  + Directional business case
* Portfolio Analysis and Migration Planning
  + Baselined complete portfolio of application and infrastructure including application dependencies
  + Baselined 7R disposition tree and application prioritization criteria
  + Baselined migration wave plan and dependency groups for the entire portfolio of in-scope applications
  + Selection of up to 5 pilot applications (subset of the entire portfolio)
  + Detailed assessment of current state (deep dive), target AWS architecture design, and migration strategy for the pilot applications
* Continuous Application Assessment
  + Detailed assessment of current state (deep dive), target AWS architecture design, and migration strategy for one migration wave (scale factor to be applied for additional waves)
  + Iterated Migration Wave Plan

Key Milestones
==============

* Migration scope identified
* Discovery tool selection and data collection
* Identify key customer stakeholders (including third-parties) to discuss application and infrastructure information (e.g., ownership, scope, strategy, requirements, outcomes)
* Installation of required tooling (if applicable) and data collection kick-off
* Initial view of the application and infrastructure inventory completed
* Pilot application candidates identified
* Directional Business Case delivered
* Baselined Applications and infrastructure inventories including dependency mapping
* Baselined migration wave plan
* Deep dive 3-5 pilot applications completed

Risks
=====

* Poorly defined migration scope of applications and infrastructure
* Delays to procure, assess and install Discovery tooling (e.g., procurement, security sign-off)
* Dependency on individuals to provide detailed application and system level details in a timely manner
* Application owners (i.e., individuals that can make decisions on the future of the application) not identified or non-existent
* Poor data collection quality
* Incomplete identification of runtime dependencies
* Vendor dependencies not fully understood
* Compliance requirements not documented

Early Decisions
===============

* Is the data from the customer sufficient for a migration or does a discovery tool need to be implemented for higher fidelity data collection?
* If discovery tooling is required, are customer security assessment required? if so, initiate those at the earliest possibility.
* Is the migration/modernization scope clear? is there a process defined to update scope in-flight?
* Can a packaged offering be utilized for discovery of specialized workloads (e.g., SAP, Large DB estate, Mainframe)
* Is a survey necessary to obtain business-level information about the applications within the portfolio or can broad assumptions be made?
* Can Licensing questions be answered and decisions made or is it necessary to perform a deeper dive into licensing (OLA/DB Freedom, etc.)?
* Can a migration strategy be proposed and accepted or is a deeper dive into Operating Model/Business Value necessary?

Epics and User Stories
======================

**Note:** the epics and user stories in this template are formatted to be imported into Jira

Decision Backlog
================

**Note:** the user stories in this template are formatted to be imported into Jira

Public References
=================

<https://docs.aws.amazon.com/prescriptive-guidance/latest/application-portfolio-assessment-guide/introduction.html>