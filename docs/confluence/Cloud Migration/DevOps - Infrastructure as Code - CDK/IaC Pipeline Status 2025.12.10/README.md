# IaC Pipeline Status 2025.12.10

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5328568482/IaC%20Pipeline%20Status%202025.12.10

**Created by:** Khalid Ahmed on December 10, 2025  
**Last modified by:** Khalid Ahmed on December 11, 2025 at 06:39 PM

---

Infrastructure Development Business Goals & User Journeys
---------------------------------------------------------

Infrastructure as Code (IaC) allows for AWS resources to be defined with AWS Cloud Development Kit (CDK) code stored in version-controlled repositories. It enables infrastructure, operations, and application teams to easily deploy AWS infrastructure with a configuration-based approach, and automates the testing and deployment of those resources. Use of standardized IaC pipelines also centralizes the function of deploying AWS resources, avoiding the need for elevated user privileges, and facilitating change management, security review, and reduced opportunity for error.

At HealthEdge, there are two primary user journeys related to IaC pipelines:

### Platform developer

As the HealthEdge cloud platform team developer, I want to define standard patterns of infrastructure, so that IT and engineering teams can deploy approved cloud resources quickly and securely.

#### Responsibilities:

* Define and maintain CDK constructs (`stacks/*.py`)
* Create reusable infrastructure patterns
* Update stack-mappings.json for resource group associations

### IT/Engineering user

As an IT or engineering user, I want to use simple YAML-based configuration to define my AWS infrastructure, so that I can iterate and innovate rapidly without having to learn AWS CDK.

#### Workflow:

1. Create or modify a YAML configuration file in config/
2. Define required globals values in config (org\_name, project\_name, environment, region)
3. Specify resource groups and their properties
4. Submit a Pull Request for validation
5. Merge to main for deployment pipeline to run

Pipeline Design
---------------

The CI/CD pipeline uses GitHub Actions to implement two core workflows:

* Test & Synth (`test-synth.yaml`) - Runs unit tests, `cdk synth` , `cdk-diff`, and `cdk-guard` and provides response in PR comment
* Deploy (`deploy.yaml`) - Performs CDK bootstrap, then runs a `cdk deploy` or `cdk-destroy` and provides response on deployed resources

### Test & Synth Pipeline Overview

Triggered on: Pull Request opened/reopened to main branch

This pipeline validates all changes before they can be merged. It performs security scanning, detects what files changed, and runs appropriate validation based on whether configuration files or CDK construct code was modified.

#### Key Capabilities:

* Secret detection to prevent credential leaks
* Filename validation for consistency
* Unit test execution for affected constructs
* CDK Synthesis to verify templates generate as expected
* CDK Diff to generate expected outcome from template
* Cloudformation Guard for compliance check
* Deleted config/construct protection
* Automated PR comments with validation results based on config or stack modifications.

![HE-IaC-Pipeline-Test_Synth_Pipeline.drawio.png](images/HE-IaC-Pipeline-Test_Synth_Pipeline.drawio.png)

### Deploy Pipeline Overview

Triggered on: Push to main branch (config file changes only)

This pipeline handles the actual deployment of infrastructure to AWS accounts. It groups configurations by environment and deploys them in parallel with appropriate environment protections.

#### Key Capabilities:

* Automatic environment detection (dev, nonprod, prod, shared)
* Pre-deployment diff preview
* Environment specific deployment gates
* CDK Deploy/Destroy to target account
* Deployment status reporting

  ![HE-IaC-Pipeline-Deploy_Pipeline.drawio.png](images/HE-IaC-Pipeline-Deploy_Pipeline.drawio.png)

### Supported Environments

The pipeline supports four target environments, each mapped to a specific AWS account in `.github/account-mapping.json`:

| **Deployment Environment** | **Config Value** |
| --- | --- |
| development | dev, development |
| nonproduction | nonprod, nonproduction |
| production | prod, production |
| shared-services | sahred, shared-services |

### Configuration File Structure

All configuration files must be placed in the `config/` directory (including subdirectories) and follow this structure:


```
globals:
    cdk_action: deploy|destroy
    org_name: "organization-name"
    project_name: "project-name"
    environment: "dev|nonprod|prod|shared"
    region: "us-east-1"
    vpc_id: "vpc-xxxxxxxx"
    
  resource_groups:
    s3_storage:
      bucket_name: "my-bucket"
      ...
    ec2_linux:
      instance_type: "t3.medium"
      ...
```


### Required Global Values

The following globals values are essential for the pipeline to function correctly. They are used to determine which AWS account to deploy to, generate a unique stack name, and configure the CDK environment. Without these values, the pipeline cannot identify the target infrastructure or execute the appropriate deployment action.

| **Field** | **Description** | **Example** |
| --- | --- | --- |
| cdk\_action | Action to perform (deploy or destroy) | deploy |
| org\_name | Organization identifier | hrp |
| project\_name | Project Identifier | delphix-resources |
| environment | AWS account for deployment | dev |
| region | AWS region for deployment | us-east-1 |

**Note**: The pipeline will fail validation if any required global value is missing. For example the stack name is auto-generated as: `{org_name}-{project_name}-{environment}-{region_short}`

### Detailed Pipeline Documentation

For in-depth documentation on each pipeline, see:

* Test Synth Pipeline - Detailed Documentation
* Deploy Pipeline - Detailed Documentation