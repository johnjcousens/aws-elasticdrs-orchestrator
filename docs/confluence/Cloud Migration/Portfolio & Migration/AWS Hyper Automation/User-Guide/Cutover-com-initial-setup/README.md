# Cutover-com-initial-setup

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4866999436/Cutover-com-initial-setup

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:18 AM

---

Cutover.com initial setup
-------------------------

### Initial Setup and Configuration

| Step | Task Name | Description | Role Owner | Requirements | Important Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | Request Cutover License on Behalf of the Customer | If using a Cutover license, an AWS delivery team member or opportunity owner will need to request a license on behalf of the customer. | ESM/Engagement Manager | * Ensure Customer has eigned a Cutover EULA prior to requesting a license * Submit a ticket via SIM and fill out all fields. You may need to work with your customer to gather some of the information. * AWS internal approver will review and approve the ticket and set up a Cutover instance within 5 business days * If the customer would like to use Cutover Connect, please indicate to the Cutover team now (~$30k to enable); see next section for guidance on Cutover Connect and other options. | Link to full instructions and information needed can be found [here](https://w.amazon.com/bin/view/AWS/Teams/Proserve/MigrationModernizationGPO/Cutover/#HHowtorequestaLicenseforanendcustomer) |
| 2 | Required Cutover Features for Hyper Automation | In order to support automation, Cutover will need to be configured with the following features. This should be requested from the cutover team as part of the customer's instance set up. | ESM/Engagement Manager | * Branching * Runbook Templates * Custom Fields * Task Type Integrations * Cutover Connect (Optional, based on deployment decision). See Architecture * Private Link (Optional, based on deployment decision). See Architecture | Link to Cutover Client Instance Configuration [Form](https://dk-knowledgebase.pages.aws.dev/dk-migration-accelerator/Delivery-Kit/Artifacts/Cutover-Client-Instance-Configuration-Form/) |
| 3 | Single Sign On (SSO) | Customer will need to establish SSO with their preferred Identity Provider (IdP). | Customer's Cutover Application Owner |  |  |
| 4 | Onboard AWS Delivery Team | Customer will need to invite and provide RBAC to AWS delivery team members. | Customer's Cutover Application Owner | * Assign AWS Delivery team members according to AWS AppSec Usage Policy * Assign customer team roles (customer establish internal RBAC) | AWS Usage Policy and Level of Access Roles by AWS AppSec [Link](https://w.amazon.com/bin/view/AWS/Teams/Proserve/MigrationModernizationGPO/Cutover/CutoverCollaborationSpace/#HUsagePolicy28AWSOnly29) |
| 5 | Create Workspaces | To get started, Cutover Workspaces will be used to host runbooks. | Customer's Cutover Application Owner OR AWS Engagement Manager | * Ensure you have role access to create workspaces * Click the '+' buttom in the bottom right corner to add a workspace * To add members, go back to the left navigation bar and click 'Access Management' * From there, you can sort by your workspace and '+' to manually or bulk upload users and assign access roles | Navigating a Workspace [Link]( https://help.cutover.com/en/articles/5850376-navigate-your-workspace) |