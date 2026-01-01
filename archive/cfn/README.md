# Archived CloudFormation Templates

This directory contains CloudFormation templates that are no longer actively used but are preserved for historical reference.

## Archived Templates

### api-stack.yaml
- **Archived Date**: December 31, 2025
- **Reason**: Replaced by `api-stack-rbac.yaml` which includes RBAC functionality
- **Replacement**: `cfn/api-stack-rbac.yaml`
- **Description**: Original API Gateway and Cognito stack without RBAC support
- **Last Used**: Prior to RBAC implementation (v1.1.0)

## Notes

- These templates are preserved for historical reference and rollback scenarios
- Do not use archived templates for new deployments
- Refer to the active `cfn/` directory for current CloudFormation templates