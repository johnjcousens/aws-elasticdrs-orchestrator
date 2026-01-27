# Bootstrapping-Cutover-co

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4866999465/Bootstrapping-Cutover-co

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:18 AM

---

Bootstrapping Cutover.com for use with the Hyper Automation Solution
====================================================================

Bootstrap
---------

A bootstrap process is required to obtain an internal integration task type and ID which is used by the Hyper Automation Solution to interact with the Cutover.com runbooks. This is a one-time activity. Follow these steps:

### Pre-Requisites for bootstrapping

* The Hyper Automation solution has been deployed (refer to

  and
* The integration between Cutover.com and Hyper Automation has been
* The callback integration has been [configured](../User-Guide/Configuring-Cutover-com-Integration.md#call-back-integration)

### Steps

**1.** Review and Import the Bootstrapping Runbook to Cutover.com. This runbook is located in [this template file](../attachments/Bootstrap-Runbook-FlowChart.drawio). Review the flow sticky notes and then upload this file to the `${ServiceName}-${AWS::AccountId}-${Environment}-templates` S3 bucket created with the solution deployment (this action will trigger the conversion of this flow into a Cutover.com templates).

**2.** In your Cutover.com workspace, go to Templates and create a runbook out of the "Cutover-Bootstrap-Runbook-1.0.0" template. Note that the name of the template could be different if you updated the metadata of the 'Start Rubook' task in the flowchart.

**3.** Open the runbook, click on the "Bootstrap hyper automation" task to see its details and:
- Change the task type from 'Normal' to the integration that was previously created (see [pre-reqs](#Pre-requisites-for-bootstrapping))
- under `CustomFields`, set the `taskAutomationId` field value to: `CUTOVER-BOOTSTRAP-AUT-001`

**4.** To start the runbook, open the runbook and click the 'play' button on the top right of your screen. When doing so, chose "live" as the Run Type and click "Start Run". Proceed to start/close initial manual tasks. To start/close a task, click on the task and scroll to the bottom of its properties in the right hand menu. Next, keep starting/closing tasks until the "Bootstrap hyper automation" task is started. Monitor its execution until it completes. Next, close any other remaining manual task until the Runbook execution is complete.

**5.** Optional. We recommend to delete or archive both the bootstrap runbook and the bootstrap runbook templates since these are no longer required.

**6.** Done. You are ready to import more runbook templates and create instantiations of these runbooks. See [How to Create Runbook Templates](../User-Guide/How-To-Create-Runbook-templates.md#how-to-convert-existent-flowchart-templates-into-cutovercom-runbook-templates)