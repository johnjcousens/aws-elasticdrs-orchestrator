# VMware Site Recovery Manager (SRM) REST API Summary

## Overview

VMware Site Recovery Manager (SRM) provides REST APIs for programmatic disaster recovery orchestration and management. These APIs enable automation of protection groups, recovery plans, and disaster recovery operations across VMware vSphere environments.

## API Architecture

### Base URL Structure
```
https://{srm-server}:{port}/dr/api/v1/
```

### Authentication
- **Method**: Session-based authentication
- **Login Endpoint**: `POST /sessions`
- **Headers**: `vmware-api-session-id` token required for subsequent requests
- **SSL**: HTTPS required for all API calls

## Core API Categories

### 1. Protection Groups API

**Purpose**: Manage groups of virtual machines that are protected together for disaster recovery.

#### Key Endpoints:
- `GET /protection-groups` - List all protection groups
- `POST /protection-groups` - Create new protection group
- `GET /protection-groups/{id}` - Get specific protection group details
- `PUT /protection-groups/{id}` - Update protection group configuration
- `DELETE /protection-groups/{id}` - Delete protection group
- `POST /protection-groups/{id}/configure` - Configure protection for VMs
- `POST /protection-groups/{id}/unconfigure` - Remove protection

#### Use Cases:
- Organize VMs by application tier (web, app, database)
- Define replication policies and RPO settings
- Manage VM protection status and dependencies

### 2. Recovery Plans API

**Purpose**: Define and manage multi-step recovery procedures with wave-based execution.

#### Key Endpoints:
- `GET /recovery-plans` - List all recovery plans
- `POST /recovery-plans` - Create new recovery plan
- `GET /recovery-plans/{id}` - Get recovery plan details
- `PUT /recovery-plans/{id}` - Update recovery plan
- `DELETE /recovery-plans/{id}` - Delete recovery plan
- `POST /recovery-plans/{id}/test` - Execute test recovery
- `POST /recovery-plans/{id}/recovery` - Execute actual recovery
- `POST /recovery-plans/{id}/reprotect` - Reprotect after recovery

#### Wave Management:
- `GET /recovery-plans/{id}/waves` - List recovery waves
- `POST /recovery-plans/{id}/waves` - Add new wave
- `PUT /recovery-plans/{id}/waves/{wave-id}` - Update wave configuration
- `DELETE /recovery-plans/{id}/waves/{wave-id}` - Remove wave

#### Use Cases:
- Define multi-tier application recovery sequences
- Configure startup dependencies between application layers
- Automate post-recovery validation and testing

### 3. Recovery Execution API

**Purpose**: Monitor and control active recovery operations.

#### Key Endpoints:
- `GET /recoveries` - List active and historical recoveries
- `GET /recoveries/{id}` - Get recovery execution details
- `POST /recoveries/{id}/pause` - Pause running recovery
- `POST /recoveries/{id}/resume` - Resume paused recovery
- `POST /recoveries/{id}/cancel` - Cancel recovery operation
- `GET /recoveries/{id}/steps` - Get detailed step execution status

#### Use Cases:
- Monitor real-time recovery progress
- Handle recovery failures and manual intervention
- Generate recovery reports and audit trails

### 4. Inventory Management API

**Purpose**: Discover and manage protected virtual machines and datastores.

#### Key Endpoints:
- `GET /inventory/vms` - List protected virtual machines
- `GET /inventory/vms/{id}` - Get VM protection details
- `GET /inventory/datastores` - List protected datastores
- `GET /inventory/networks` - List available networks for recovery
- `GET /inventory/folders` - List VM folders and organization

#### Use Cases:
- Discover VMs available for protection
- Validate recovery target resources
- Map source to target infrastructure

### 5. Site Management API

**Purpose**: Manage protected and recovery sites configuration.

#### Key Endpoints:
- `GET /sites` - List configured sites
- `GET /sites/{id}` - Get site configuration details
- `POST /sites/{id}/pair` - Establish site pairing
- `DELETE /sites/{id}/unpair` - Remove site pairing
- `GET /sites/{id}/status` - Check site connectivity status

#### Use Cases:
- Configure multi-site disaster recovery
- Monitor site-to-site connectivity
- Manage failover and failback operations

## Common API Patterns

### Request/Response Format
```json
// Request Headers
{
  "Content-Type": "application/json",
  "vmware-api-session-id": "session-token",
  "Accept": "application/json"
}

// Typical Response Structure
{
  "id": "protection-group-123",
  "name": "WebTier-PG",
  "description": "Web tier protection group",
  "state": "configured",
  "vms": [
    {
      "id": "vm-456",
      "name": "web-server-01",
      "protectionState": "protected"
    }
  ],
  "createdTime": "2024-01-15T10:30:00Z",
  "modifiedTime": "2024-01-15T14:20:00Z"
}
```

### Error Handling
```json
{
  "error": {
    "code": "INVALID_ARGUMENT",
    "message": "Protection group name already exists",
    "details": [
      {
        "field": "name",
        "issue": "Duplicate name not allowed"
      }
    ]
  }
}
```

## Authentication Flow

### 1. Login and Get Session Token
```bash
curl -X POST https://srm-server/dr/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@vsphere.local",
    "password": "password"
  }'
```

### 2. Use Session Token
```bash
curl -X GET https://srm-server/dr/api/v1/protection-groups \
  -H "vmware-api-session-id: session-token-here"
```

### 3. Logout
```bash
curl -X DELETE https://srm-server/dr/api/v1/sessions/current \
  -H "vmware-api-session-id: session-token-here"
```

## Integration Patterns

### 1. Automated Protection Group Creation
```python
# Pseudo-code example
def create_protection_group(srm_client, name, vm_list):
    pg_config = {
        "name": name,
        "description": f"Auto-created PG for {name}",
        "vms": [{"id": vm_id} for vm_id in vm_list]
    }
    
    response = srm_client.post("/protection-groups", json=pg_config)
    pg_id = response.json()["id"]
    
    # Configure protection
    srm_client.post(f"/protection-groups/{pg_id}/configure")
    return pg_id
```

### 2. Recovery Plan Execution
```python
def execute_recovery_plan(srm_client, plan_id, recovery_type="test"):
    execution_config = {
        "recoveryType": recovery_type,  # "test" or "recovery"
        "syncData": True,
        "powerOnVms": True
    }
    
    response = srm_client.post(f"/recovery-plans/{plan_id}/{recovery_type}", 
                              json=execution_config)
    recovery_id = response.json()["recoveryId"]
    
    # Monitor progress
    while True:
        status = srm_client.get(f"/recoveries/{recovery_id}")
        if status.json()["state"] in ["completed", "failed"]:
            break
        time.sleep(30)
    
    return status.json()
```

## API Capabilities vs AWS DRS

| Feature | VMware SRM API | AWS DRS API | Notes |
|---------|----------------|-------------|-------|
| Protection Groups | ✅ Full CRUD | ✅ Full CRUD | Similar concepts |
| Recovery Plans | ✅ Wave-based | ✅ Launch templates | SRM more advanced |
| Real-time Monitoring | ✅ Detailed steps | ✅ Job tracking | Both provide status |
| Test Recovery | ✅ Non-disruptive | ✅ Drill mode | Core DR capability |
| Automation Hooks | ✅ Custom scripts | ✅ SSM integration | Different approaches |
| Cross-site Management | ✅ Built-in | ✅ Cross-account | Architecture differs |

## Common Use Cases

### 1. Disaster Recovery Automation
- Automated failover based on monitoring alerts
- Scheduled DR testing and validation
- Compliance reporting and audit trails

### 2. Application-Aware Recovery
- Multi-tier application orchestration
- Database consistency and startup ordering
- Network reconfiguration and IP management

### 3. DevOps Integration
- CI/CD pipeline integration for DR testing
- Infrastructure as Code for DR configurations
- Automated recovery plan updates

### 4. Monitoring and Alerting
- Real-time recovery progress tracking
- Integration with ITSM systems
- Custom dashboards and reporting

## API Limitations and Considerations

### Rate Limiting
- Typical limit: 100 requests per minute per session
- Bulk operations recommended for large environments
- Async operations for long-running tasks

### Permissions
- Role-based access control (RBAC) required
- Separate permissions for read vs. write operations
- Site-specific permissions for multi-site deployments

### Version Compatibility
- API versions tied to SRM product versions
- Backward compatibility maintained within major versions
- Feature availability varies by SRM edition

## Documentation and Resources

### Official VMware Documentation
- **SRM REST API Guide**: https://docs.vmware.com/en/Site-Recovery-Manager/8.6/srm-rest-api-guide.pdf
- **SRM Administration Guide**: https://docs.vmware.com/en/Site-Recovery-Manager/
- **vSphere API Reference**: https://developer.vmware.com/apis/vsphere-automation/

### Developer Resources
- **VMware Developer Portal**: https://developer.vmware.com/
- **SRM PowerCLI Cmdlets**: https://developer.vmware.com/powercli/
- **REST API Explorer**: Available in SRM web interface under Developer Tools

### Community Resources
- **VMware Communities**: https://communities.vmware.com/t5/Site-Recovery-Manager/bd-p/2016-SRM
- **GitHub Examples**: https://github.com/vmware/vsphere-automation-sdk-rest
- **PowerShell Gallery**: https://www.powershellgallery.com/packages/VMware.PowerCLI

### Training and Certification
- **VMware Learning**: https://www.vmware.com/education-services/
- **SRM Specialist Certification**: Available through VMware Education
- **Hands-on Labs**: https://labs.hol.vmware.com/

## Comparison with AWS DRS Orchestration Solution

### Similarities
- **Protection Groups**: Both organize servers/VMs for recovery
- **Recovery Plans**: Both support multi-wave execution
- **API-First**: Both provide comprehensive REST APIs
- **Monitoring**: Both offer real-time execution tracking

### Key Differences
- **Architecture**: SRM is on-premises, AWS DRS is cloud-native
- **Automation**: SRM uses custom scripts, AWS DRS uses SSM
- **Scaling**: SRM limited by hardware, AWS DRS serverless
- **Integration**: SRM with vSphere, AWS DRS with AWS services

### Migration Considerations
When migrating from VMware SRM to AWS DRS:
1. **Protection Groups** map directly to DRS Protection Groups
2. **Recovery Plans** require wave configuration translation
3. **Custom scripts** need conversion to SSM documents
4. **Monitoring** integrates with CloudWatch instead of vCenter

## Conclusion

VMware SRM REST APIs provide comprehensive disaster recovery orchestration capabilities for VMware environments. The APIs enable automation of protection, recovery, and monitoring workflows similar to what the AWS DRS Orchestration solution provides for AWS environments. Understanding SRM API patterns helps in designing equivalent functionality for cloud-native disaster recovery solutions.

---

**Last Updated**: November 20, 2025  
**Document Version**: 1.0  
**Author**: AWS DRS Orchestration Solution Documentation