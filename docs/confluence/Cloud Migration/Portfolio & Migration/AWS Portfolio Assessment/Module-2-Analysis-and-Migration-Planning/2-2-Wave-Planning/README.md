# 2-2-Wave-Planning

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867065712/2-2-Wave-Planning

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:50 AM

---

---

title: 2.2 Wave Planning
------------------------

Introduction
============

The migration wave plan is one of the main deliverables of an Application Portfolio Assessment. It has to be approached incrementally as it requires several iterations, even beyond the first baselined version. To be successful at wave planning, you will require a combination of data and tools.

Pre-Requisites
--------------

* An inventory of in-scope applications and infrastructure, including application to infrastructure mapping.
* An application prioritization criteria
* A list of available technical and non-technical resources (people), their skill set, and availability.
* An understanding of customer business outcomes, inclusive of desired completion dates, key deadlines, and milestones.
* Infrastructure/Application communication data or architectural data establishing how applications interact between them and what are the key data flows.

Tooling
-------

* Discovery tool of choice and/or other sources of information (e.g., App Performance Monitoring, Observability data, CMDBs).
* [Migration Portfolio Assessment](https://mpa.accelerate.amazonaws.com/) (MPA) (Link available to AWS Employees and Partners). Used to create dependency groups, waves, and perform group to wave assignment.
* [Wave Planning Tool](https://amazon.awsapps.com/workdocs/index.html#/folder/fe692b87c65d82c3b1b19f05f0be0d8cf96c56a6766a547b9a5cb1627b4ce640) (Link available to AWS Employees). Used to refine the MPA plan and perform detailed planning (resource plan, effort calculation, and refined schedule).

Output
======

A baselined wave plan will contain the following:

* A schedule of migration waves
* The effort estimation per wave
* A resource plan to deliver the wave schedule
* A list of dependency groups assigned to waves
* A list of applications/infrastructure assigned to dependency groups

The output of the [Wave Planning Tool](https://amazon.awsapps.com/workdocs/index.html#/folder/fe692b87c65d82c3b1b19f05f0be0d8cf96c56a6766a547b9a5cb1627b4ce640) (Link available to AWS Employees) will contain all of the above.

High-level steps
================

1. Define initial wave plan structure
2. Create dependency groups and assign groups to waves
3. Calculate effort based on migration strategy/pattern
4. Refine resources and overall plan

**Follow the guidelines below for details.**

Guidelines
==========

Start with socializing the following definitions:

* **Soft Dependency:** is a relationship between two or more assets such as servers, containers, applications, etc. that is not dependent on the location of the interacting components. For example, two systems that operate in the same local network (or same infrastructure) can be split apart by moving one of those systems to the cloud whilst the other remains on-premises. The communication can continue, with no impact to functional/non-functional requirements, over WAN links such as Direct Connect.
* **Hard Dependency:** is a relationship between two or more assets such as servers, containers, applications, etc. that is dependent on location. For example, two systems that operate in the same local network and that are heavily dependent on low latency for communication (e.g., application server and database server). Moving only one of these systems to the cloud would cause functionality/performance problems that cannot be resolved. Likewise, non-technical reasons such as resource availability (e.g., team performing the migration) or operational constraints might create a hard dependency between assets. For example, moving two applications that are dependant to each other in different waves would cause a double outage experience that is not practical or acceptable.
* **Dependency Groups:** these are composed of assets that must be migrated at the same time due to dependencies that cannot be resolved (i.e., hard dependencies). Groups will be combined into waves. A dependency group can be as small as containing one application and one server, or as large as containing several applications and dozens of servers.
* **Migration Waves:** consist of one or more dependency groups and span a period of time that could range from days to weeks or months. Waves are aligned to a criteria in order to define its duration and the groups they will contain. For example, waves can be aligned to business outcomes. Ideally, the completion of a wave should reflect a measurable achievement. In some cases, other criteria can be used to create waves. For example, crating waves by environment, or by migration strategy.

Creating the initial Wave Plan Structure
----------------------------------------

At this stage you might already have a portfolio in [MPA](https://mpa.accelerate.amazonaws.com/). If that is not the case, then proceed to create a portfolio and import all applications, servers, and databases from the in-scope application/infrastructure inventory. It is key to also import application-to-server and application-to-database mapping.

Next, start with analyzing dates to create an initial high-level structure of empty waves in [MPA](https://mpa.accelerate.amazonaws.com/). You can use the option to automatically create waves based on an estimated overall migration duration (e.g., 1 year) by specifying migration start and end dates, wave duration (e.g., 5 weeks), and the number of waves (e.g., 10). These waves can be updated later on, including adding or removing waves. At this stage, you want to define an initial and estimated structure. To estimate dates (initially) consider the following:

* What is the total migration program length? What are the deadlines? Fixed Data Center exit dates? Co-location contract end dates? Refresh cycles? Application release cycles? Change freezes? Holiday periods?
* Are there any dates where migrations should be avoided? (e.g., end of year, holidays, business events, release cycles)
* What is the default wave length? Note: smaller waves are preferable (e.g., 6 weeks). Wave length will be a function of the time required to complete the migration of one or more dependency groups, including the time to assess/design the AWS target architecture, create migration runbooks and cutover planning, setup migration tooling, time to replicate data, operational readiness, time to perform the cut-over, test and go live/roll-back, and post-migration operational handover and wave closure.

Note that, in general, waves are not fully sequential and tend to overlap slightly. This is in order to accelerate the migration process. The key to overlapped waves is to define and consider what happens within a wave (see diagram below). Typically, deployment activities, platform validation, and data synchronization will occur during the first half of a wave. The second half will focus on cut-over preparation, the actual migration, testing, operational handover, and post migration optimization. This means that different teams are involved in the process and therefore some efficiencies can be gained.  For example, as soon as the team involved in platform preparation has completed their work they can start working on the requirements of the next wave.

Also, note that although we chose an arbitrary wave duration at the start of the wave planning process, as the plan is refined not all waves will have the same duration. Later in the wave planning process, the duration of a given wave will be recalculated in order to match requirements, size, and skilled resource capacity. In general, it is preferable that most waves have a similar duration and structure in order to facilitate a factory-like approach to migrations, but this is not always possible.

Understanding what occurs inside a wave
---------------------------------------

In order to achieve effective planning, it is key to understand the migration process. The following diagram illustrates the different stages within a wave:

Analyzing dependencies and creating dependency groups
-----------------------------------------------------

As defined at the top of this page, dependency groups are groups of assets that must be migrated at the same time (e.g., during the same cutover window). Dependency groups can be made of just 1 application and its infrastructure or several applications/infrastructure. The key is to understand that what goes into a dependency group is treated as a migration atomic unit. This segmentation will help when iterating the plan. For example, if at some point, one application has to be moved to a different wave, it is not just the application that is moved but the entire dependency group. Creating dependency groups also forces the review of relevant dependencies that otherwise could be missed.

Dependency groups can be created in [MPA](https://mpa.accelerate.amazonaws.com/) by importing application-to-application dependencies and/or server communication data. Note that it is mandatory to have application-to-server and application-to-database mappings as stated in 'Creating the initial Wave Plan Structure' section above. In MPA, infrastructure can only be added to dependency groups via its link to applications. By default, if application-to-application and server communication data are not uploaded to the MPA portfolio, MPA will create one dependency group per application. Be cognisant of chains of dependencies since these can create large dependency groups. For example, If appA is linked to AppB, and AppB linked to AppC, then all three apps will be in the same group.

If you are using server communication data (e.g., server to server traffic information) in MPA be mindful that these datasets are typically verbose and include all types of traffic, which will blur real dependencies. This will lead to a chain a dependencies and very large dependency groups. Some of these communications might be between application servers and shared infrastructure services, such as DNS or Active Directory, that can create false dependency groups. This is something that will require filtering common infrastructure traffic out from the imported dataset, and then iterate the dependency groups to continue to remove traffic that does not represent a real dependency that meets our definition.

When analyzing dependencies, consider these questions:

* Can these dependencies be ignored?
* Can these applications be removed from the group?
* Is there any shared service?
* Is there a missed dependency that forces incorporating more applications into a group?

As dependency groups are baselined, proceed to add them to waves in MPA. To determine which groups to add to each wave (from a timeline point of view), use the MPA application prioritization feature (see 

Artifact - Application Prioritization Criteria
). Then order your dependency groups based on prioritization ranking, and proceed to add them to waves. This process will require several iterations. Also, consider wave capacity based on available resources to execute the migration and try to keep waves of a size that matches the velocity that your resource plan supports. You can further iterate wave composition in the next step.

**Note:** wave size is typically dictated by risk appetite (e.g., how much parallel change can be tolerated), and resource availability (e.g., how much parallel change can be performed with the available resources and budget). However, do not be limited by resource requirements/availability during early planning, waves that contain more than one dependency group can be decomposed into smaller waves later on, if needed.

**Note 2:** the portfolio of applications and infrastructure will change during the lifecycle of the migration program. This is expected and should be managed. Scope changes will affect Dependency Groups and Waves. It is key to establish a scope control mechanism in order to handle change and minimize impact. It is expected that the scope of a wave or dependency group will require changes, especially closer to the migration date when a previously unknown dependency is identified or a new server is included to or removed from the inventory. Sometimes, scope changes happen during the cutover itself. Long-running migration programs coexist with normal business evolution and change. Applications keep evolving as they wait to migrated. Servers are added/removed, new infrastructure is deployed on-premises, etc. A wave plan must be prepared to handle these changes.

A scope change control mechanisms requires the definition of a single source of truth for the scope (your inventory). The key is to identify changes, analyze impact, and communicate change to the relevant stakeholders to take action. The wave plan will be iterated as a result.

Refining resources and the overall plan
---------------------------------------

Once the Dependency Groups have been defined and assigned to your initial set of waves, proceed to further iterate the plan using the [Wave Planning Tool](https://amazon.awsapps.com/workdocs/index.html#/folder/fe692b87c65d82c3b1b19f05f0be0d8cf96c56a6766a547b9a5cb1627b4ce640) (Link available to AWS Employees). To do so, export the MPA plan (Plan → Migration Waves → Download Wave Report). Next, follow the instructions of the Wave Planning Tools (Actions sheet) to import the MPA plan, set the planning inputs, and calculate assets, resources, and waves.

The Wave Planning Tool will help you to define the level of effort per each Wave phase at both, application level, and infrastructure level, per each migration strategy/pattern. The tool supports up to 12 distinct strategy/pattern effort models.

In addition, you will define a resource plan based on a list of resources, their skills, and availability. Next, you will be able to calculate, automatically, the actual start/end dates of each wave based on your resource plan. This will help you to make changes and iterate the plan until you reach a desired schedule. The tool has the option to override the automatic dates calculation if needed. Also, you can increase/decrease the complexity factor of each wave. For example, the initial waves could be considered more difficult whilst subsequent waves will become easier as migration experience is gained. Some waves could have specific requirements (such as compliance) that requires additional effort.

When calculating resources, consider adjusting the wave size (i.e., dependency groups it contains) based on resource availability and tool results. Initially you might have considered larger or smaller waves than what your actual migration throughput supports. Work with the Migration workstream to define the level of effort and skill required to migrate each wave. The tool will consider resource availability and parallel work in order to calculate recommended wave duration.

**Attachments:**

[WaveConstruct.drawio.png](../../attachments/WaveConstruct.drawio.png)