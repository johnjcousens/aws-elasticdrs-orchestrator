# VMware Site Recovery Manager (SRM) REST API Summary

A comprehensive reference for VMware SRM REST API endpoints used in disaster recovery orchestration.

## Overview

VMware Site Recovery Manager provides REST APIs for managing protection groups, recovery plans, and disaster recovery operations between vSphere sites.

## Authentication

VMware SRM uses session-based authentication:

```bash
# Login to get session token
POST https://srm-server.example.com/api/sessions
Authorization: Basic <base64-encoded-credentials>
```

## Base URL Structure

```
https://srm-server.example.com/api/
```

## Protection Groups Management

### List Protection Groups

**Endpoint**: `GET /protection-groups`

**Purpose**: Retrieve all protection groups

**Response**:
```json
{
  "protection_groups": [
    {
      "id": "pg-12345",
      "name": "WebServers-PG",
      "description": "Web tier protection group",
      "type": "san",
      "state": "ready",
      "peer_state": "ready",
      "protection_state": "shadowing",
      "vm_count": 5,
      "datastore_count": 2,
      "recovery_plan_count": 1,
      "last_test_time": "2024-01-15T10:30:00Z",
      "vms": [
        {
          "vm_id": "vm-001",
          "name": "web-server-01",
          "protection_state": "shadowing",
          "needs_configuration": false
        }
      ]
    }
  ]
}
```

### Create Protection Group

**Endpoint**: `POST /protection-groups`

**Request**:
```json
{
  "name": "DatabaseServers-PG",
  "description": "Database tier protection group",
  "type": "san",
  "input_spec": {
    "datastore_groups": [
      {
        "datastores": ["datastore-001", "datastore-002"]
      }
    ]
  }
}
```

### Get Protection Group Details

**Endpoint**: `GET /protection-groups/{pg-id}`

**Response**:
```json
{
  "id": "pg-12345",
  "name": "WebServers-PG",
  "state": "ready",
  "protection_state": "shadowing",
  "vm_count": 5,
  "vms": [
    {
      "vm_id": "vm-001",
      "name": "web-server-01",
      "protection_state": "shadowing",
      "placeholder_vm_id": "vm-placeholder-001",
      "recovery_settings": {
        "priority": "high",
        "startup_delay": 0,
        "shutdown_delay": 300
      }
    }
  ],
  "datastores": [
    {
      "datastore_id": "ds-001",
      "name": "WebServers-DS",
      "capacity_gb": 500,
      "used_gb": 250
    }
  ]
}
```

## Recovery Plans Management

### List Recovery Plans

**Endpoint**: `GET /recovery-plans`

**Response**:
```json
{
  "recovery_plans": [
    {
      "id": "rp-12345",
      "name": "WebApp-Recovery-Plan",
      "description": "Complete web application recovery",
      "state": "ready",
      "peer_state": "ready",
      "protection_group_count": 3,
      "vm_count": 15,
      "last_test_time": "2024-01-10T14:00:00Z",
      "last_test_result": "success",
      "recovery_priority_groups": [
        {
          "priority": 1,
          "name": "Database Tier",
          "vm_count": 2
        },
        {
          "priority": 2,
          "name": "Application Tier",
          "vm_count": 8
        },
        {
          "priority": 3,
          "name": "Web Tier",
          "vm_count": 5
        }
      ]
    }
  ]
}
```

### Create Recovery Plan

**Endpoint**: `POST /recovery-plans`

**Request**:
```json
{
  "name": "WebApp-Recovery-Plan",
  "description": "Complete web application recovery",
  "protection_groups": [
    {
      "protection_group_id": "pg-12345",
      "recovery_priority_group": {
        "priority": 1,
        "name": "Database Tier"
      }
    },
    {
      "protection_group_id": "pg-12346",
      "recovery_priority_group": {
        "priority": 2,
        "name": "Application Tier"
      }
    }
  ]
}
```

### Get Recovery Plan Details

**Endpoint**: `GET /recovery-plans/{rp-id}`

**Response**:
```json
{
  "id": "rp-12345",
  "name": "WebApp-Recovery-Plan",
  "state": "ready",
  "protection_groups": [
    {
      "protection_group_id": "pg-12345",
      "name": "WebServers-PG",
      "recovery_priority_group": {
        "priority": 1,
        "name": "Database Tier",
        "startup_delay": 0,
        "shutdown_delay": 300
      }
    }
  ],
  "recovery_settings": {
    "default_vm_priority": "medium",
    "default_startup_delay": 0,
    "default_shutdown_delay": 300,
    "callout_commands": [
      {
        "command": "health-check.sh",
        "timeout": 300,
        "run_on": "recovery_site"
      }
    ]
  }
}
```

## Recovery Execution

### Start Recovery (Test/Planned/Emergency)

**Endpoint**: `POST /recovery-plans/{rp-id}/recovery`

**Request**:
```json
{
  "recovery_type": "test",
  "sync_data": true,
  "recovery_options": {
    "power_on_vms": true,
    "customize_failover": false,
    "recovery_point_policy": "latest"
  }
}
```

**Response**:
```json
{
  "task_id": "task-12345",
  "recovery_type": "test",
  "state": "running",
  "start_time": "2024-01-15T14:30:00Z",
  "progress_percent": 0,
  "result_state": "running",
  "recovery_history_id": "rh-12345"
}
```

### Monitor Recovery Progress

**Endpoint**: `GET /recovery-plans/{rp-id}/recovery-history/{rh-id}`

**Response**:
```json
{
  "id": "rh-12345",
  "recovery_plan_id": "rp-12345",
  "recovery_type": "test",
  "state": "completed",
  "result_state": "success",
  "start_time": "2024-01-15T14:30:00Z",
  "end_time": "2024-01-15T14:45:00Z",
  "progress_percent": 100,
  "recovery_priority_groups": [
    {
      "priority": 1,
      "name": "Database Tier",
      "state": "completed",
      "result_state": "success",
      "vm_recoveries": [
        {
          "vm_id": "vm-001",
          "vm_name": "db-server-01",
          "state": "completed",
          "result_state": "success",
          "recovery_vm_id": "vm-recovery-001",
          "power_state": "poweredOn"
        }
      ]
    }
  ]
}
```

### Cleanup Test Recovery

**Endpoint**: `POST /recovery-plans/{rp-id}/cleanup`

**Request**:
```json
{
  "recovery_history_id": "rh-12345"
}
```

## Reprotection and Failback

### Start Reprotection

**Endpoint**: `POST /recovery-plans/{rp-id}/reprotect`

**Request**:
```json
{
  "recovery_history_id": "rh-12345",
  "reverse_replication": true
}
```

### Planned Failover

**Endpoint**: `POST /recovery-plans/{rp-id}/planned-failover`

**Request**:
```json
{
  "sync_data": true,
  "shutdown_source_vms": true
}
```

## Virtual Machine Management

### List Protected VMs

**Endpoint**: `GET /vms`

**Response**:
```json
{
  "vms": [
    {
      "vm_id": "vm-001",
      "name": "web-server-01",
      "protection_group_id": "pg-12345",
      "protection_state": "shadowing",
      "needs_configuration": false,
      "placeholder_vm_id": "vm-placeholder-001",
      "recovery_settings": {
        "priority": "high",
        "startup_delay": 0,
        "shutdown_delay": 300,
        "ip_customization": {
          "enabled": true,
          "ip_address": "10.0.2.100",
          "subnet_mask": "255.255.255.0",
          "gateway": "10.0.2.1"
        }
      }
    }
  ]
}
```

### Configure VM Recovery Settings

**Endpoint**: `PUT /vms/{vm-id}/recovery-settings`

**Request**:
```json
{
  "priority": "high",
  "startup_delay": 60,
  "shutdown_delay": 300,
  "ip_customization": {
    "enabled": true,
    "ip_address": "10.0.2.100",
    "subnet_mask": "255.255.255.0",
    "gateway": "10.0.2.1",
    "dns_servers": ["10.0.2.10", "10.0.2.11"]
  },
  "custom_properties": {
    "application_startup_script": "/opt/app/startup.sh",
    "health_check_url": "http://localhost:8080/health"
  }
}
```

## Site Management

### List Sites

**Endpoint**: `GET /sites`

**Response**:
```json
{
  "sites": [
    {
      "site_id": "site-001",
      "name": "Primary-Site",
      "type": "protected",
      "state": "connected",
      "vcenter_server": "vcenter-primary.example.com",
      "srm_server": "srm-primary.example.com"
    },
    {
      "site_id": "site-002",
      "name": "Recovery-Site",
      "type": "recovery",
      "state": "connected",
      "vcenter_server": "vcenter-recovery.example.com",
      "srm_server": "srm-recovery.example.com"
    }
  ]
}
```

### Get Site Pairing Status

**Endpoint**: `GET /sites/{site-id}/pairing`

**Response**:
```json
{
  "local_site_id": "site-001",
  "remote_site_id": "site-002",
  "pairing_state": "paired",
  "connection_state": "connected",
  "last_heartbeat": "2024-01-15T14:30:00Z",
  "replication_health": "healthy"
}
```

## Inventory Management

### List Datastores

**Endpoint**: `GET /datastores`

**Response**:
```json
{
  "datastores": [
    {
      "datastore_id": "ds-001",
      "name": "WebServers-DS",
      "type": "vmfs",
      "capacity_gb": 500,
      "used_gb": 250,
      "protection_group_id": "pg-12345",
      "replication_state": "synced"
    }
  ]
}
```

### List Resource Pools

**Endpoint**: `GET /resource-pools`

**Response**:
```json
{
  "resource_pools": [
    {
      "resource_pool_id": "rp-001",
      "name": "Production-RP",
      "cpu_limit_mhz": 10000,
      "memory_limit_mb": 32768,
      "vm_count": 15
    }
  ]
}
```

## Compliance and Reporting

### Get Recovery Plan Test History

**Endpoint**: `GET /recovery-plans/{rp-id}/test-history`

**Response**:
```json
{
  "test_history": [
    {
      "test_id": "test-001",
      "test_date": "2024-01-10T14:00:00Z",
      "result": "success",
      "duration_minutes": 15,
      "vms_recovered": 15,
      "vms_failed": 0,
      "rpo_achieved": "PT5M",
      "rto_achieved": "PT15M"
    }
  ]
}
```

### Generate Compliance Report

**Endpoint**: `POST /reports/compliance`

**Request**:
```json
{
  "report_type": "rpo_rto_compliance",
  "date_range": {
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z"
  },
  "recovery_plans": ["rp-12345", "rp-12346"]
}
```

## Error Handling

### Common Error Responses

**Invalid Request**:
```json
{
  "error_type": "INVALID_REQUEST",
  "message": "Protection group name already exists",
  "details": {
    "field": "name",
    "value": "WebServers-PG"
  }
}
```

**Resource Not Found**:
```json
{
  "error_type": "NOT_FOUND",
  "message": "Recovery plan rp-99999 not found"
}
```

**Operation Not Allowed**:
```json
{
  "error_type": "OPERATION_NOT_ALLOWED",
  "message": "Cannot start recovery while test is in progress",
  "current_state": "test_running"
}
```

## PowerCLI Integration Examples

### Connect to SRM

```powershell
# Connect to vCenter and SRM
Connect-VIServer -Server vcenter.example.com
Connect-SrmServer -SrmServer srm.example.com

# Get protection groups
$protectionGroups = Get-ProtectionGroup
```

### Execute Recovery Plan

```powershell
# Get recovery plan
$recoveryPlan = Get-RecoveryPlan -Name "WebApp-Recovery-Plan"

# Start test recovery
$testTask = Start-RecoveryPlan -RecoveryPlan $recoveryPlan -RecoveryMode Test

# Monitor progress
do {
    Start-Sleep -Seconds 30
    $task = Get-Task -Id $testTask.Id
    Write-Host "Progress: $($task.PercentComplete)%"
} while ($task.State -eq "Running")

# Cleanup test
Stop-RecoveryPlan -RecoveryPlan $recoveryPlan -CleanupTest
```

## Best Practices

### API Usage Guidelines

1. **Session Management**: Maintain active sessions and handle timeouts
2. **Polling Intervals**: Use appropriate intervals for monitoring operations
3. **Error Handling**: Implement retry logic for transient failures
4. **Resource Limits**: Respect API rate limits and concurrent operation limits
5. **State Validation**: Always check resource states before operations

### Recovery Plan Design

1. **Priority Groups**: Use priority groups for dependency management
2. **Startup Delays**: Configure appropriate delays between VM startups
3. **Network Customization**: Plan IP address schemes for recovery site
4. **Testing Schedule**: Regular testing to validate recovery procedures
5. **Documentation**: Maintain runbooks for manual intervention scenarios

This VMware SRM API reference provides the foundation for understanding SRM's disaster recovery orchestration capabilities and serves as a comparison point for AWS DRS functionality.