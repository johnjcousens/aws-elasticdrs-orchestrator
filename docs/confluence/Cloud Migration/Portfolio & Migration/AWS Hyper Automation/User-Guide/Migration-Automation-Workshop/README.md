# Migration-Automation-Workshop

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867097101/Migration-Automation-Workshop

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:19 AM

---

Migration Automation Workshop Delivery Guidance
-----------------------------------------------

### Goals and Pre-Requisites

The primary outcome of the Migration Automation Workshop is to work with the customer to outline a process to automate as many migration tasks as a customer can support for their migration. Automations can come pre-packaged and ready from the Automation Library, or can be built as custom automations. This workshop will spend dedicated time identifying areas that could potentially be automated to help free up time and personnel. Overall, we want to drive and communicate the value that can be created for the customer by using automations in order to remove bottlenecks and drive for a faster, more efficient migration.

While pre-requisites aren’t necessary to conduct the Migration Automation Workshop, Discovery Acceleration and Planning (DAP) and Landing Zone Assessment are helpful inputs to drive the conversation with the customer. These inputs are especially helpful during the Landing Zone and and Rehost runbook portions of the workshop.

This workshop will take place over two days with the customer. In that, the key outputs for the workshop are as follows:

**1.** Migration scope and patterns understood at a high-level
**2.** Implications of LZ design to migration velocity
**3.** Rehost/Replatform process documented
**4.** Custom automations identified, assessed and prioritized
**5.** Backlog for next steps

Attendees
---------

The following list of attendees should be invited and ready to participate over the next two days. This should be delivered as a shared session between AWS and the customer working together to identify places of automation.

| Resouece | Role | Attendance |
| --- | --- | --- |
| AWS Resource | ESM/Practice Manager | Required |
| AWS Resource | CDA | Required |
| AWS Resource | CIA | Required |
| AWS Resource | Migration Consultant | Required |
| AWS Resource | AppDev Consultant / DevOps Consultant | Required |
| AWS Resource | Security Consultant | Required |
| Customer Resource | Application Owners | Optional |
| Customer Resource | Cloud Program Owner/Main Sponsor | Required |
| Customer Resource | Enterprise Architect(s) and/or Tehnical Lead(s) | Required |
| Customer Resource | Application Architects | Optional |
| Customer Resource | Cloud Platform Lead | Required |
| Customer Resource | Cloud Platform SME's | Required |
| Customer Resource | On-prem platform SMEs (Compute, Database, Storage) | Required |
| Customer Resource | On-prem Network SMEs | Required |
| Customer Resource | InfoSec | Required |
| Customer Resource | Service Management Operations | Required |
| Customer Resource | Observability/Monitoring | Required |
| Partner Resources | Partners | Optional |

Discovery Workshop Checklist
----------------------------

* (Optional) Complete Discovery Acceleration & Planning (DAP) - 6 weeks prior
* (Optional) Complete Landing Zone Assessment - 2 weeks prior
* Gather customer CMDB and/or discovery data- 2 weeks prior
* Establish the logistics for hosting the session (e.g., remote or office location) - 2 weeks prior
* Review tactical and strategic goals of the event; discuss expected friction points - 1.5 weeks prior
* Preview expectations with the attending leaders of each domain (security, applications, etc.) - 1 week prior
* Document assigned roles and expected attendees by session / tracks - 1 week prior
* Confirm attendees from the customer who will represent roles and responsibilities listed in attendees (see agenda). These attendees should be a mix of doers and decision makers - 1 week prior
* Confirm logistics for the meeting (single meeting room for all participants or preferred customer tool for virtual collaboration) - 1 week prior

Migration Automation Workshop Session
-------------------------------------

Day 1
-----

| Recommended Start Times | Duration Minutes | Topic | Considerations | Delivery Guidance | Objectives |
| --- | --- | --- | --- | --- | --- |
| 9:00 am | 60 | Intros, goal setting and business outcomes | The customer Cloud Programme Owner and/or Main sponsor should be a CO-LEAD of the workshop. | Keep this time to introduce everyone, review agenda and hear from the customer sponsor to align and gather the voice of the customer. | Objectives: 1/Introduce attendees, 2/Review Workshop agenda, 3/Voice of the Customer: high-level Business drivers and customer outcomes (e.g., cost reduction, DC Exit, etc.) |
| 10:00 am | 60 | Migration Scope | Document metadata gaps to later inform the need of discovery tooling when preparing a proposal | This session is focused on reviewing the documentation or representation of the scope of work to be discussed. Ideally, this should be a review of data to ensure nothing is missing from the migration scope. If the scope is not yet understod, it would be worth reviewing the customer's CMDB. This should be a rather simple scope review to create alignment, ask any questions, and discuss what actions need to be taken to ensure the scope is clear. | Objectives: 1/Overview of application and infrastructure scope, including criteria to determine what is in and out of scope. 2/Review existent metadata (e.g., CMDB, inventories, server lists). |
| 11:00 am | 30 | End-to-End Automation Demo |  | The end-to-end automation demo can be delivered as a pre-recorded session, or delivered directly through the Cutover.com training instance. Overall, the demo will show the 'behind the scenes' of how all pre-built and custom automations will take plce. |  |
| 11:30 am | 60 | Discussion/Review: Landing Zone | The LZ design could impact automation efforts, for example by requiring further transformation of migrated workloads to meet cloud onboarding requirements. The intention of this session is to understand potential constraints of a desired LZ design and subsequent recommendations. In addtion, LZ requirements can impact migration velocity, for example, the availability of a given capability, such as 3rd party load balancers, could influence the scope that is ready to migrate by a given date. LZ capabilities, if released over a given timeline, should be planned in such a way that prevents a dry out of a migration pipeline. | See 'Considerations' for the Landing Zone discussion. Do not try to repeat activities from Landing Zone assessment if it has been completed, but instead have a single person available to talk through teh current LZ design | Objectives: 1/is this Greenfield or Brownfield?, 2/Understand customer appetite to deploy an AWS-recommended LZ (e.g., LZA) vs own design, 3/Review LZ design (or discuss intentions), 4/Discuss potential impact to migration velocity and automation |
| 12:30 PM | 45 | Lunch Break |  |  |  |
| 1:15 pm | 120 | Rehost and Replatform process/runbook | In some cases, AWS might have information of previous migrations performed by the customer with ProServe or SAs. If this is the case, there should be an internal processing of any existent process/runbook in advance of the workshop to ensure we are starting from what we know and avoid repetitive questions. | During this session, the team should review the existing rehost/replatfrom runbook and work with their customer to determine the true 'end-to-end' migration process they need to take. From the template runbook, the goal is to review what additional tasks need to take place in order to form a customized runbook. It's importand to tailor the runbook to customer's internal processes and overall tasks they need to complete internally (i.e. raising change requests, etc.) It's worth noting, too, that some tasks in the template runbook can be expanded out and split into multiple tasks where needed. By the end of the session, the goal is not to have a perfect runbook. The goal is to get to a better migration process that can be iterated upon. | Objectives: 1/Review standard Rehost and Replatform process, 2/Identify required vs non-required tasks, 3/Identify additional tasks and customer specific tasks, 4/Note tasks that might split into more detailed tasks, 5/Identify automation opportunities (out-of-the-box automations vs custom automations), 6/ Document potential requirements from customer side to increase automation levels. |
| 3:15 PM | 15 | Break |  |  |  |
| 3:30 pm | 90 | Rehost and Replatform process/runbook (continued) | Might not be enough time to review all tasks, so key time-consuming tasks should be prioritized |  | Objectives: 1/Review input/output data requirements per task, including data sources and data stores, 2/Identify end-to-end automation key requirements |
| 5:00 pm | 30 | Wrap-up |  | Close the day with a short recap of what was accomplished, and what will be completed in the following day. | Objectives: Review outcomes and next steps |

Day 2
-----

| Recommended Start Times | Duration Minutes | Topic | Considerations | Delivery Guidance | Objectives |
| --- | --- | --- | --- | --- | --- |
| 9:00 am | 30 | Goal setting for the day |  | Close the day with a short recap of what was accomplished, and what will be completed in the following day. | Objectives: Review outcomes and next steps |
| 9:30 am | 90 | End-To-End Automation High-level design |  | This session will be led by someone who can technically walk thr customer through how the customer will be deploying an automation in their account. | Objectives: 1/Review end-to-end automation architecture, components, security considerations, and data flows, 2/Review requirements for solution deployment |
| 11:00 am | 90 | End-To-End Automation - Custom automation - Part 1 | Focus on tasks that are currently not automated and that show potential for process effiency. Prioritize high-value tasks. | Based on the runbook template developed the day before, the customer and delivery team can begin to identify some candidates of tasks that can be automated. It's important to show the customer in this session how we can remove bottlenecks for them as we progress through the migration. Ideally the teams should be focusing on custom and customer-specific automations we could automate for them. | Objectives: 1/Review customer specific tasks and how to automate them |
| 12:30 PM | 45 | Lunch Break |  |  |
| 1:15 PM | 90 | End-To-End Automation - Custom automation - Part 2 | Focus on tasks that are currently not automated and that show potential for process effiency. Prioritize high-value tasks. |  | Objectives: 1/Review customer specific tasks and how to automate them |
| 2:45 pm | 90 | Create Automation Backlog | The goal of this session is for each workstream to understand their role in the hyper automation migration and to indentify key activities to enable hyper automation, including process efficiency (business as usual vs. migration) | Someone with agile-experience should leas this session. Based on all the info collected over the past two days, we will need to work with the cstomer to create a backlog of next steps and actions we can take. We will want representation from every team to come in and 'build their backlog' for their workstream based on their best estimate of the work to be completed. | Objectives: 1/Organize different sub-teams by area (e.g., runbook management, landing zone, migration, security) and produce an initial backlog of key activities per workstream. |
| 4:15 pm | 45 | Sub-teams backlog presentaiton (10 min each max) |  | Based on the previous session, we will want to give tome to each workspream to present their backlog to the wider team. | Objectives: Each sub-team to provide a high-level overview of key backlog items |
| 5:00 pm | 30 | Wrap-Up: Review Outcomes and Next Steps |  | As part of wrap up, we will review the outcomes achoeved over the past two days and identify the next steps to be taken as part of their engagement. |  |