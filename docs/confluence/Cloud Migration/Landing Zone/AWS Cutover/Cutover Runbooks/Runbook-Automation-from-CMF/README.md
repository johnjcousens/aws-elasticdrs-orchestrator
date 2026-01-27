# Runbook-Automation-from-CMF

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867032776/Runbook-Automation-from-CMF

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:15 AM

---

---

title: Automation - runbook creation and wave scope management from CMF
-----------------------------------------------------------------------

Introduction
============

In large scale migration projects the scope of hundreds, thousands or ten of thousands of migration units (Servers, Databases, Containers, etc) introduces a significant administration overhead. These challenges include, management of a changing wave scope, creation of runbooks for all the different applications and migration patterns, along with the synchronization of these change across different tools and repositories.

To simplify some of this process we have introduced a new automation capability for projects using the Cloud Migration Factory on AWS (CMF) solution, that integrates the inventory held in CMF with the runbook capabilities of Cutover.

The automation provides the following capabilities when initiated:
- Automatically creates Wave and Application runbooks in Cutover, based on the Waves and applications defined in CMF.
- Creates a Waves folder structure in Cutover mirroring that of CMF.
- Ensures that any change in Wave scope is mirrored between CMF and Cutover.

Pre-requisites
--------------

* CMF instance deployed.
* CMF Automation Server running, with outbound internet access to Cutover instance being used.

Setup Instructions
------------------

### Within the Cutover Instance

1. Open Cutover, go to Access Management.
2. Create a new user (press the big plus button).
3. Enter the first name as CMF, as last name as Automation.
4. Enter an email address (Note: this is not used as this is a non-interactive user.)
5. For the roles select:
6. Developer
7. Workspace manager > [your migration workspace]
8. Workspace runbook creator > [your migration workspace]
9. Workspace stakeholder > [your migration workspace]
10. On the Login option
11. Select Non Interactive
12. Click Create
13. Once created open the new user
14. Click on the User App Tokens
15. Click the Create user app token
    1. Add the label of CMF
    2. Capture the new user token presented on the screen. This wil be needed in the next section within CMF.

### Within CMF Instance

#### Setup Cutover credentials in Credentials Manager

1. Open the CMF Instance Web UI (Administrator rights is required).
2. Navigate to **Administration** > **Credential Manager**.
3. Choose **Add**.
4. Choose the **Secret Type** of **Secret key/value**.
5. Enter a **Secret Name** of your choosing.
6. Enter the full URL for the Cutover instance into the **Key** field.
7. Paste the user token capture earlier into the **Value** field.
8. Enter a description for the new credential.
9. Choose **Save**

#### Add CMF Cutover Automation Script

1. Download the CMF script file from.
2. Open the CMF Instance Web UI (Administrator rights is required).
3. Navigate to **Automation** > **Scripts**.
4. Choose **Add**
5. Choose **Select file** and then select the Cutover CMF script package zip file.
6. Choose **Next**.
7. Leave script name empty.
8. Choose **Upload**

Using the automation
--------------------

1. Open the CMF Instance Web UI
2. Navigate to **Automation** > **Jobs**.
3. Choose **Actions** > **Run Automation**.
4. Enter a **Job Name** of your choice.
5. Select the **Automation Server** where the script will run.
6. Select the **Script Name**, **Create runbooks in Cutover**. This will then display the parameters for the automation.
7. Select the **Cutover API Secret** created in Credentials Manager.
8. The remainder of the parameters are optional, you should verify that the default values match your Cutover instance; if not then you will need to provided them here.
9. Choose **Submit Automation Job**
10. Once Submitted, view the status of the job from the **Jobs** view. Choose refresh to see the latest status.