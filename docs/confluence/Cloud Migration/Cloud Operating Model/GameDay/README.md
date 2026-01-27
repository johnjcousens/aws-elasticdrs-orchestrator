# GameDay

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4866083939/GameDay

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:03 AM

---

Overview
--------

The Operations Game Day assesses and improves a customer's operational readiness by planning and delivering operations scenarios in the customers AWS account and for a specific application / workload that is migrated in the project.  Like a fire drill, game day scenarios are operational events that can be triggered in a customer environment to test their operational capability. The events assess the customer's operational processes, tools, and people involved in a "production ready" environment. Operations Game Days can be utilized by customers in the early stages of a migration to plan for operational activities before an application is migrated, in order to increase business confidence & operational alignment or if there is a need to modernize their operational approaches.  Game days can be initiated by running intrusive scripts ( test operational processes and troubleshooting), or by lowering alarm thresholds (test operational processes).

The core Operations Game Day scenarios cover the Incident and Event Management design implemented for the operations workstream.  The scope of AWS services that is addressed is generally limited to EC2 as well as possibly RDS or another dependent service for the workload.  and provide the option for extending the scope to address other domains with an incremental growth in effort.

Game Day Scenario Framework
---------------------------

The following diagram provides an overview of game days in general. More details on the operation specific activities can be found in the below section:

![](../../attachments/Screen%20Shot%202020-02-05%20at%2010.16.20%20AM.png)

User Stories & Tasks
--------------------

The Operations Game Day can be subdivided into 4 stories with related tasks spanning learning, preparing, delivering, and reviewing as follows:

1. As an Operations Leader, I want to increase my operational readiness by l**earning** about AWS ProServe Game Days and how they can help my teams.

   1. Identify operational stakeholders to support your game days
   2. Kick off game day preparation with education on what game days are and how they differ from other AWS game days
   3. Customize approach based on stakeholder requirements
   4. Obtain stakeholder support to work with the team (important to get this buy in as game days are involve a lot of preparation and you will need as much help as you can get)
2. As an Operations Leader, I want to increase my operational readiness by **preparing** my teams for an operations game day event.

   1. Identify participants and participant roles and responsibilities
   2. Set logistics & time frame (rooms, dates, whiteboards, phones, pagers)
   3. Obtain access to environment
   4. Finalize game day Scenario (EC2 and RDS to start off)
   5. Communicate about the game day event and confirm you have critical mass to conduct the event (schedule, notice outlook declines/accepts)
3. As an Operations Leader, I want to increase my operational readiness by **delivering** a game day event

   1. Communicate the event and make sure you have all necessary stakeholders from customer informed and confirmed as well as AWS (enterprise support, managed service support, etc)
   2. Run pre game day event with planning team (review if you have everything needed)
   3. Trigger game day events using automation if testing processes and troubleshooting using stress tool

      * EC2 sample scripts provided separately
      * RDS sample game day provided separately
   4. Trigger game days by lowering alarm thresholds if only testing processes
   5. Observe and record game day process (SLA, time taken to resolve, areas of improvement)
   6. Close the event with an EBA type of activity if possible (prizes, happy hour, something to bring the team together)
4. As an Operations Leader, I want to increase my operational readiness by **reviewing** results of my game day event.

   1. Gather feedback from participants and provide event feedback documentation
   2. Organize a debrief with planning team/stakeholders and sponsors
   3. Use Operations Playbook to provide feedback in closeout Template
   4. Use results to plan a roadmap

Effort
------

The effort for the game day spans planning, delivery, and review for one Incident and Event Management scenario involving EC2 as well as a potential additional service such as RDS.

Offering
--------

The Operations Game Day offering aligns operations perspective of the Cloud Adoption Framework.

The key assets for supporting learning, preparation, and review are:

* Game Day Scenario Overview

* Game Day Planning

* Building a Custom Game Day

* Game Day Review