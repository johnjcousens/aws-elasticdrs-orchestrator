# Using-And-Deploying-Automations

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4866999562/Using-And-Deploying-Automations

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:19 AM

---

Using, Creating, and Deploying Automations
------------------------------------------

You can both leverage existing automations and create your own.

### Package Structre

`modules/aes_automations` this directory contains all Lambda automations.

`modules/cmf_automation_packages/` this directory contains CMF Custom automation scripts

### AWS Lambda vs CMF custom automation

You will determine this by understanding what needs to be automated. If the automation logic can be performed in a Lambda function, then place your logic in lambda. See [How to create new automations (AWS Lambda)](#how-to-create-new-automations-aws-lambda) for more details.
If your automation needs to run from a server (e.g., to intall software) and cannot run from AWS Lambda, then you can leverage CMF Custom automations and still invoke them from a Cutover.com Runbook. CMF custom automations will run from the Automation Server. See See [How to create new automations (CMF Custom Automation)](#how-to-create-new-automations-cmf-custom-automation) for more information about creating CMF Custom automations.

### Using existing automations

The table below contains a list of automations included with this solution. Once you have identified the automations to use in your Runbook proceed to set the corresponding automation ID in the task metadata of your FlowChart Runbook template (e.g., your drawIO Runbook FlowChart) or directly in the Cutover.com runbook template task. (see

for more information). Keep in mind that these automations are meant to be invoked from a Cutover.com Runbook.

Note that each automation has its own readme file in the automation library repo. Refer to those informations for mode details. The table below contains a high-level description only.

**Important Note** automations with id "MIG-CMF-AUT-XXX" are executed in the Automation Server

to apply selectivelly to Dependency Groups within a Wave it is required to use Cloud Migration Factory v3.3.5 or above. For earlier versions of CMF, these automations will apply to the entire wave even when a Dependency Group is specified in the source data. To workaround this limitation in older verions of CMF we recommend to use smaller waves equivalent to dependency groups, for example, by using wave suffixes such as Wave-1-Group-1 when defining the wave name.

| Automation ID | Task Name | Description |
| --- | --- | --- |
| MIG-CMF-EXCEL-IMPORT | Import data to CMF | This automation is designed to import data from excel/csv into CMF through an AWS Lambda function. It expects a known excel template (provided with the delivery kit attachments) in the relevant S3 bucket for storing these files (`...-cmf-excel-import-artifacts` bucket) |
| MIG-CMF-AUT-001 | 1-Install MGN Agents | This automation calls CMF APIs to trigger the installation of MGN agents on source servers in a given wave or dependency group (as defined in the CMF metadata store) |
| MIG-CMF-AUT-002 | 2-Verify Replication Status | This automation calls CMF APIs to trigger the verification of the replication status for the server in a given wave or dependency group (as defined in the CMF metadata store). This automation is implemented as a step function to keep verifying until data replication is complete. |
| MIG-CMF-AUT-003 | 1-Copy Post Launch Scripts | This automation calls CMF APIs to trigger the automation to copy files to the MGN folder in the local server. |
| MIG-CMF-AUT-004 | 3-Verify Instance Status | This automation calls CMF APIs to trigger the verification of the status of migrated instances (i.e., status of EC2 2/2 checks). |
| MIG-CMF-AUT-005 | 3-Shutdown All Servers | This automation calls CMF APIs to trigger the shutdown of all servers in a given wave or dependency group (as defined in the CMF metadata store) |
| MIG-CMF-AUT-006 | 0-State Capture and Services Management - capturestop | This automation has been developed as a CMF custom automation (in order to leverage the automation servers to access on-prem servers) and it is triggered by calling the CMF APIs. Its purpose is to capture state of running processes in source servers and gracefully stop applications and DB services before cut over. |
| MIG-CMF-AUT-007 | 0-State Capture and Services Management - capturestart | This automation has been developed as a CMF custom automation (in order to leverage the automation servers to access on-prem servers) and it is triggered by calling the CMF APIs. Its purpose is to start application and DB services after migration, based on the captured previous state. |
| MIG-CMF-MGN-001 | Validate Launch Template | This automation calls CMF APIs to trigger the verification of MGN launch templates in a given wave or dependency group (as defined in the CMF metadata store) |
| MIG-CMF-MGN-002 | Launch Test Instances | This automation calls CMF APIs to trigger the launch of MGN test instances in a given wave or dependency group (as defined in the CMF metadata store). |
| MIG-CMF-MGN-003 | Revert to ready for testing | This automation calls CMF APIs to revert the MGN status to the test cycle for a given wave or dependency group (as defined in the CMF metadata store). |
| MIG-CMF-MGN-004 | Terminate Launched instances | This automation calls CMF APIs to trigger the verification of MGN launched instances for a given wave or dependency group (as defined in the CMF metadata store). |
| MIG-CMF-MGN-005 | Mark as Ready for Cutover | This automation calls CMF APIs to mark MGN instances as ready for cutover for a given wave or dependency group (as defined in the CMF metadata store). |
| MIG-CMF-MGN-006 | Launch Cutover Instances | This automation calls CMF APIs to trigger the launch of MGN cutover instances in a given wave or dependency group (as defined in the CMF metadata store). |
| MIG-CMF-MGN-007 | Finalize Cutover | This automation calls CMF APIs to finalize the cutover process for servers in a given wave or dependency group (as defined in the CMF metadata store). |
| MIG-CMF-MGN-008 | Revert to ready for cutover | This automation calls CMF APIs to revert the status of MGN to ready for cutover for a given wave or dependency group (as defined in the CMF metadata store). |

How to create new automations (AWS Lambda)
------------------------------------------

**1.** Copy the `modules/aes_automations/sample_automation` folder into a new folder named `modules/aes_automations/<my_automation_name>`

**2.** Update the event rule in `modules/aes_automations/<my_automation_name>/automation.template.yaml`, replacing MIG-TEST-01 with a new automation ID defined by you and not yet used in other other automations.

**3.** Edit the following code to reflect your stake name (replace `<my_automation_stack_name>` with your stak name) and update the TemplateURL property with the correct path to your automation template. Next, copy the block to the bottom of `modules/automations_stack.template.yaml`

`<my_automation_stack_name>:
Type: AWS::CloudFormation::Stack
DependsOn:
- AesStack
Properties:
TemplateURL: './aes_automations/<my_automation_name>/automation.template.yaml'
Parameters:
AutomationLayerArn: !GetAtt AutomationLayerStack.Outputs.AutomationLayerArn`

Configure your automation according to your needs. You'll probably need to:
- Modify the lambda source
- Define your automation logic and actions
- Integrate with downstream systems such as customer On-premises resources, etc.
- Use the provided data clients to retrieve and store data in the metadatastore. See

for more information.
- Add new permissions to the IAM policy

* And possibly
  + Add secrets to secret manager to authenticate to systems not integrated with IAM

How to create new automations (CMF Custom Automation)
-----------------------------------------------------

There's two supported methods for creating CMF custom automations.

### Deploying CMF Custom Automations using the CMF WEB UI

Follow this [CMF instructions for managing custom scripts](https://docs.aws.amazon.com/solutions/latest/cloud-migration-factory-on-aws/scripts-management.html)
You can leverage the sample package in `modules/cmf_automation_packages/automations/0-cmf-automation-package-sample`

### Deploying CMF Custom Automations via automations

This document explains the provided Makefile, which automates building and uploading custom CMF Automation Packages to an S3 bucket. Locate the Makefile in `modules/cmf_automation_packages/`

It's integrated into the deployment process triggered by the `npm run deploy:root --env={env}` command.

#### Prerequisites

* An AWS account with appropriate permissions for S3 access.
* The `aws` CLI tool installed and configured with your AWS credentials.
* Node.js and npm (or yarn) installed on your development machine.

#### Directory Structure

This Makefile assumes the following directory structure for your project:

* `./automations`: This directory should contain the source code for your custom CMF Automation scripts. Each script should reside in a separate subdirectory within this folder. You can leverage the sample package in `modules/cmf_automation_packages/automations/0-cmf-automation-package-sample`
* `./zips`: This directory will be used to store the generated zip files containing your Automation Packages. It's created automatically during build.

#### Building Packages

To build a new custom CMF Automation Package, simply place the script files and any relevant resources under a subdirectory within the `./automations` directory.

The Makefile provides a target named `zip-files` which iterates through subdirectories under `./automations` and creates a zip file for each one. These zip files will be placed in the `./zips` directory.

#### Uploading Packages to S3

The `sync-to-s3` target handles uploading the generated zip files to an S3 bucket. Here's what it does:

**1.** It loops through each zip file in the `./zips` directory.
**2.** For each file, it checks if a file with the same name already exists in the designated S3 bucket (identified by the `S3_BUCKET` variable).
**3.** If the file doesn't exist in S3, it's uploaded for the first time.
**4.** If the file already exists, the Makefile calculates the MD5 checksum of the local zip file and compares it with the ETag retrieved from the S3 object using the `aws s3api head-object` command.
**5.** If the MD5 checksums match, it indicates that the file hasn't changed, and the upload is skipped.
**6.** If the MD5 checksums differ, it signifies an update, and the local zip file is uploaded to overwrite the existing one in S3.

#### Running the Deployment Script

To build, upload your custom CMF Automation Packages, and potentially deploy your application, run the following command in your terminal:

`bash
npm run deploy:root --env={env}`

Replace `{env}` with the appropriate deployment environment name.

### Invoking CMF Custom Automations

The solution comes with an overaching automation that can process CMF custom automation IDs and trigger the desired CMF custom automation. Once your new CMF Custom Automation is deployed, proceed to make it available to Cutover.com by adding it to the `modules/aes_automations/automation-cmf-automation-jobs` automation, as follows:

**1.** Modify `modules/aes_automations/automation_cmf_automation_jobs/src/automation_jobs.py` to define a new function that matches your new automation

**2.** Modyfy `modules/aes_automations/automation_cmf_automation_jobs/automation.template.yaml` by editing this portion of the template, adding the ID of your new automation to the list of the Event Rule:
`Resources:
CMFStartAutomationRule:
Type: AWS::Events::Rule
Properties:
EventBusName: HyperAutomationAesEventBus
EventPattern:
source:
- 'com.cutover.aws-training.ingressRouter'
detail:
taskAutomationId:
- MIG-CMF-AUT-001
- MIG-CMF-AUT-002
- MIG-CMF-AUT-003
- MIG-CMF-AUT-004
- MIG-CMF-AUT-005
- MIG-CMF-AUT-006
- MIG-CMF-AUT-007
- <MY NEW ID>`

**3.** Modify the AWS LAmbda handler function in `modules/aes_automations/automation_cmf_automation_jobs/src/index.py` to include your automation. See sample portion of the code below:
`# Check the script_name and set script arguments accordingly
script_config_generator = {
"MIG-CMF-AUT-001": {
"config_function": get_install_mgn_agents_config,
"script_name": "1-Install MGN Agents",
},
"MIG-CMF-AUT-002": {
"config_function": get_verify_replication_status_config,
"script_name": "2-Verify Replication Status",
},
"MIG-CMF-AUT-003": {
"config_function": get_copy_post_launch_scripts_config,
"script_name": "1-Copy Post Launch Scripts",
},
"MIG-CMF-AUT-004": {
"config_function": get_verify_instance_status_config,
"script_name": "3-Verify Instance Status",
},
"MIG-CMF-AUT-005": {
"config_function": get_shutdown_all_servers_config,
"script_name": "3-Shutdown All Servers",
},
"MIG-CMF-AUT-006": {
"config_function": get_state_capture_and_services_capturestop_config,
"script_name": "0-state-capture-and-services-management",
},
"MIG-CMF-AUT-007": {
"config_function": get_state_capture_and_services_start_config,
"script_name": "0-state-capture-and-services-management",
},
"<MY NEW ID>": {
"config_function": ,name_of_the_function_in_automations_jos_py.,
"script_name": <"name_of_my_new_cmf_custom_script">,
},
# Add more entries as needed for different automation jobs
}`

**4.** After deploying the above changes, you can reference and invoke your new custom automation from Cutover.com using the automation ID you defined

### Creating a new version of an automation (AWS Lambda)

If you want to mutate an existing automation, you have a few options:

**1.** Mutate the existing automation in place.
- Just update the lambda source and re-deploy.

**2.** Create a new automation as a new module

```
- Copy the ```modules/<base_automation>``` folder into a new folder named ```modules/<new_automation>```
- Follow steps 2-4 to for creating a new automation
```

**3.** Create a new automation within an existing module

```
- Simply create a new lambda handler/entrypoint and add that lambda to your stack, with a new MIG assigned.
```

### Creating a long running automation with AWS Step Functions

Long running automations can be supported with stepfunctions. See `modules/aes_automations/sample_step_automation` for an example.

Supported Automation Runtimes
-----------------------------

The following runtimes are supported for automations:

* Python lambdas
* Python step functions
* Scripts run via the CMF automation server
  + Should be initiated by a python lambda
  + If task is long running, can poll the status with step functions

Task resuming
-------------

Automations can optionally return a failure context on task failure. This is shown in cutover and used for resuming a task. For example if we are performing step X on servers 1-5, and server 2 and 3 fail, then the failure context might be [2, 3], and resent to that automation. It is on the automation developer to write automations to behave correctly if the failure context is provided, e.g. only performing step X on servers 2, 3.

Authenticating automations to on-prem systems
---------------------------------------------

On premises systems and other non-iam guarded systems might need to be accessed by automations. Any secrets needed to authenticate to non-iam guarded systems should be stored in secrets manager. Different systems use different authentication methods, but for the most part will require the distribution of some secret value or private key.

**1.** Create a new secret in the automation.template.yaml stack.
`<my-secret-name>:
Type: AWS::SecretsManager::Secret
Properties:
# DO NOT ADD ANY CONFIDENTIAL SECRETS, PRIVATE KEYS, OR PASSWORDS HERE. LEAVE THE SECRET VALUE EMPTY
Name: <my-secret-name>`
Be sure to replace `<my-secret-name>` accordingly.

**2.** Add permissions for your lambda automation to read that secret
```

in your existing lambda/step function role(s)
=============================================

* PolicyName: GetSecretPolicy
  PolicyDocument:
  Version: 'October 17, 2012'
  Statement:
  - Effect: Allow
  Action:
  - secretsmanager:GetSecretValue
  Resource: !Sub arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:
  `Be sure to replace```` accordingly.

**3.** Set the secret value using the aws console.

```
- Open the AWS Console
- Navigate to your new secret `<my-secret-name>`
- Set the secret
```

Configuring Email Notifications:
--------------------------------

* Setup your SMTP server using your email server.
* -Open the AWS Console
* -Navigate to the secret NotificationsSMTPCredentials
* -Fill in the secret with the following values:
  `{
  "smtp_server":"...", // contact your email administrator for this value
  "smtp_port":"...", // contact your email administrator for this value
  "smtp_username":"...", // contact your email administrator for this value
  "smtp_password":"...", // contact your email administrator for this value
  "is_smtps_server":"true/false", // does the server supports the smtps protocol on the specified port, otherwise smtp will be used when initializing the connection to the server
  "sender_email":"..." // the address to show as the sender for all emails
  }`

Add the 'notificationRecipient' property to the integration payload to be the email address of the person to notify when a task fails or times out.

Building new modules
--------------------

This repository has a monorepo structure. Any new modules should go in the ./modules directory. We take the design philosophy that if a module requires a build process, it should be defined within that module alone. There should Also be a process to clean up any build artifacts within a module. We have choose to use makefiles for this as each module might use different tooling, have different artifacts, etc. When writing make files, create build and clean recipes.

Automation Traceability
-----------------------

The @automation wrapper provides logging. These logs can be used to determine which automations ran when. There will be a start message for each invocation of each automation, queryable via the following attributes:

* taskAutomationId
* taskId
* taskInternalId
* taskName
* runbookId
* runbookName

For example, if you want to query which automations have been called from runbook '123', you would navigate to the log group for the automation(s) you would like to explore and run the following query:
`fields @timestamp, @message, @logStream, @log
| filter message.runbookId = "123"`

Personal Account Deployment
---------------------------

For personal testing, create a parameter file named environments/local.json, using the format of the parameter files in that directory. Then, set export npm\_config\_env=local in your shell before you run npm run deploy:root

VPC Access for Automations
--------------------------

To enable access of private vpc resources to automations, you should configure the automations to run in a vpc. Simply provide values for the VpcId and SubnetId stack parameters and the lambda function will automatically be placed in the corresponding vpc.

Strategies to retry tasks in Cutover.com
----------------------------------------

Suppose you write an automation that has to run operation X on 20 servers server1, server2, ..., server20. If this task succeeds on some subset of these servers, e.g. all servers except server7 and server11. This task would be marked as failed, but in reality it mostly succeeded.

### Strategy 1: Idempotency (recommended)

If you write operation X to be idempotent, you can simply retry the task on all servers. For example, if operation X is installing a migration agent onto a server:
```
servers: list[string]

for server in servers:
if not isAgentInstalled(server): # so that the automation can be rerun arbitrarily
installAgent(server)
```

### Strategy 2: Partial retry with parameters

Sometimes its difficult to write operations to be idempotent. In this case, when the automation is rerun, we need to provide that automation a list of what servers on which to perform operation X. In this case, you have to somehow signal to that automation that only a subset of servers need to be run. One way of doing this is to add a parameter to the cutover.com integration called servers. When an automation fails, return the list of failed servers in the error message. When a task fails, simply create a new task that send the servers parameter to your automation. Of course, you need to write your automation such that if servers are given, operation X is only performed on those servers.

### Strategy 3: Partial retry with Runbook Data Layer

Another option is to modify your automation such that for all successful servers, a completed attribute is set on that server in the CMF data store using RDL. You rewrite your automation to check for that completed attribute before performing operation X on a particular server.