# Disaster Recovery API Reference

A comprehensive reference for disaster recovery orchestration APIs and patterns used in enterprise DR solutions.

> **Last Updated**: December 2024
> **Purpose**: API patterns and best practices for disaster recovery orchestration
> **Scope**: Generic DR concepts applicable across platforms

## Overview

This document provides API patterns and concepts commonly used in disaster recovery orchestration platforms. It serves as a reference for understanding DR automation patterns and can be used to compare different DR solutions and their capabilities.

## Common DR API Categories

| Category | Purpose |
|----------|---------|
| Authentication | Session management and security |
| Protection Groups | Logical grouping of protected resources |
| Recovery Plans | Orchestration definitions and execution |
| Recovery Operations | Test, planned, and emergency recovery |
| Reprotection | Failback and reverse replication |
| Virtual Machines | Protected resource management |
| Sites | Multi-site configuration and status |
| Inventory | Infrastructure resources and mappings |
| Tasks | Async operation monitoring |
| Reports | Compliance and audit trails |

---

## Authentication Patterns

Most enterprise DR solutions use session-based authentication with integration to identity providers.

### Typical Session Creation

**Endpoint Pattern**: `POST /api/sessions`

**Headers**:

```text
Authorization: Basic <base64-encoded-credentials>
Content-Type: application/json
```

**Response Pattern**:

```json
{
    "session_id": "session-12345",
    "user": "administrator@company.com",
    "created_time": "2024-01-15T10:00:00Z",
    "expires_time": "2024-01-15T18:00:00Z"
}
```

**Subsequent Requests**: Include session token in header:

```text
session-token: session-12345
```

### Session Termination

**Endpoint Pattern**: `DELETE /api/sessions`

---

## Base URL Structure

```text
https://{dr-server}/api/
```

## Protection Groups Management

Protection Groups represent logical collections of resources that are protected and recovered together.

### List Protection Groups

**Endpoint Pattern**: `GET /api/protection-groups`

**Query Parameters**:

- `filter_property` - Property to filter by
- `filter` - Filter value
- `sort_by` - Sort field
- `sort_order` - ASC or DESC

**Response Pattern**:

```json
{
    "list": [
        {
            "id": "protection-group-1",
            "name": "WebServers-PG",
            "description": "Web tier protection group",
            "type": "replication",
            "state": "ready",
            "peer_state": "ready",
            "protection_state": "protected",
            "resource_count": 5,
            "storage_count": 2,
            "recovery_plan_count": 1,
            "last_test_time": "2024-01-15T10:30:00Z",
            "fault": null
        }
    ],
    "paging_info": {
        "total_count": 10,
        "page_size": 25,
        "page_number": 1
    }
}
```

**Protection Group Types**: `replication`, `snapshot`, `continuous`

**Protection States**: `not_configured`, `partially_configured`, `protected`, `not_protected`

### Create Protection Group

**Endpoint Pattern**: `POST /api/protection-groups`

**Request Pattern**:

```json
{
    "name": "DatabaseServers-PG",
    "description": "Database tier protection group",
    "type": "replication",
    "input_spec": {
        "storage_groups": [
            {
                "source_storage": ["storage-001", "storage-002"],
                "target_storage": "storage-recovery-001"
            }
        ]
    }
}
```

**Continuous Replication Protection Group**:

```json
{
    "name": "AppServers-PG",
    "description": "Application tier with continuous replication",
    "type": "continuous",
    "input_spec": {
        "resources": ["resource-001", "resource-002", "resource-003"],
        "replication_settings": {
            "rpo_minutes": 15,
            "point_in_time_instances": 24,
            "consistency_groups": true
        }
    }
}
```

### Get Protection Group Details

**Endpoint**: `GET /api/protection-groups/{pg-id}`

**Response**:

```json
{
    "id": "protection-group-1",
    "name": "WebServers-PG",
    "description": "Web tier protection group",
    "type": "san",
    "state": "ready",
    "peer_state": "ready",
    "protection_state": "shadowing",
    "vm_count": 5,
    "vms": [
        {
            "vm_id": "vm-001",
            "name": "web-server-01",
            "protection_state": "shadowing",
            "placeholder_vm_id": "vm-placeholder-001",
            "needs_configuration": false,
            "fault": null
        }
    ],
    "datastores": [
        {
            "datastore_id": "ds-001",
            "name": "WebServers-DS",
            "capacity_bytes": 536870912000,
            "free_bytes": 268435456000,
            "replication_state": "synced"
        }
    ],
    "recovery_plans": ["rp-12345"]
}
```

### Update Protection Group

**Endpoint**: `PUT /api/protection-groups/{pg-id}`

**Request**:

```json
{
    "name": "WebServers-PG-Updated",
    "description": "Updated description"
}
```

### Delete Protection Group

**Endpoint**: `DELETE /api/protection-groups/{pg-id}`

**Query Parameters**:

- `force` - Force deletion even if VMs are protected (boolean)

### Add VMs to Protection Group

**Endpoint**: `POST /api/protection-groups/{pg-id}/vms`

**Request**:

```json
{
    "vms": ["vm-004", "vm-005"]
}
```

### Remove VMs from Protection Group

**Endpoint**: `DELETE /api/protection-groups/{pg-id}/vms/{vm-id}`

---

## Recovery Plans Management

### List Recovery Plans

**Endpoint**: `GET /api/recovery-plans`

**Response**:

```json
{
    "list": [
        {
            "id": "recovery-plan-1",
            "name": "WebApp-Recovery-Plan",
            "description": "Complete web application recovery",
            "state": "ready",
            "peer_state": "ready",
            "protection_group_count": 3,
            "vm_count": 15,
            "last_test_time": "2024-01-10T14:00:00Z",
            "last_test_result": "success",
            "last_recovery_time": null,
            "last_recovery_result": null,
            "fault": null
        }
    ]
}
```

**Recovery Plan States**: `ready`, `not_ready`, `running`, `prompting`, `error`

### Create Recovery Plan

**Endpoint**: `POST /api/recovery-plans`

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
        },
        {
            "protection_group_id": "pg-12347",
            "recovery_priority_group": {
                "priority": 3,
                "name": "Web Tier"
            }
        }
    ],
    "recovery_settings": {
        "default_vm_priority": "normal",
        "default_startup_delay_seconds": 0,
        "default_shutdown_delay_seconds": 300
    }
}
```

### Get Recovery Plan Details

**Endpoint**: `GET /api/recovery-plans/{rp-id}`

**Response**:

```json
{
    "id": "recovery-plan-1",
    "name": "WebApp-Recovery-Plan",
    "description": "Complete web application recovery",
    "state": "ready",
    "peer_state": "ready",
    "protection_groups": [
        {
            "protection_group_id": "pg-12345",
            "name": "DatabaseServers-PG",
            "recovery_priority_group": {
                "priority": 1,
                "name": "Database Tier"
            }
        }
    ],
    "recovery_priority_groups": [
        {
            "priority": 1,
            "name": "Database Tier",
            "vm_count": 2,
            "pre_power_on_steps": [],
            "post_power_on_steps": []
        },
        {
            "priority": 2,
            "name": "Application Tier",
            "vm_count": 8,
            "pre_power_on_steps": [
                {
                    "step_type": "command",
                    "name": "Wait for DB",
                    "command": "/scripts/wait-for-db.sh",
                    "timeout_seconds": 300,
                    "run_on_site": "recovery"
                }
            ],
            "post_power_on_steps": []
        }
    ],
    "vm_recovery_settings": [
        {
            "vm_id": "vm-001",
            "vm_name": "db-server-01",
            "priority": "high",
            "startup_delay_seconds": 0,
            "shutdown_delay_seconds": 300,
            "depends_on_vms": [],
            "ip_customization": {
                "enabled": true,
                "rules": [
                    {
                        "source_ip": "10.0.1.100",
                        "target_ip": "10.0.2.100",
                        "target_subnet": "255.255.255.0",
                        "target_gateway": "10.0.2.1"
                    }
                ]
            }
        }
    ]
}
```

### Update Recovery Plan

**Endpoint**: `PUT /api/recovery-plans/{rp-id}`

### Delete Recovery Plan

**Endpoint**: `DELETE /api/recovery-plans/{rp-id}`

### Add Protection Group to Recovery Plan

**Endpoint**: `POST /api/recovery-plans/{rp-id}/protection-groups`

**Request**:

```json
{
    "protection_group_id": "pg-12348",
    "recovery_priority_group": {
        "priority": 4,
        "name": "Monitoring Tier"
    }
}
```

### Configure Recovery Priority Groups

**Endpoint**: `PUT /api/recovery-plans/{rp-id}/priority-groups`

**Request**:

```json
{
    "priority_groups": [
        {
            "priority": 1,
            "name": "Database Tier",
            "pre_power_on_steps": [
                {
                    "step_type": "prompt",
                    "name": "Confirm DB Recovery",
                    "message": "Confirm database recovery is ready to proceed"
                }
            ],
            "post_power_on_steps": [
                {
                    "step_type": "command",
                    "name": "Verify DB Health",
                    "command": "/scripts/verify-db.sh",
                    "timeout_seconds": 600,
                    "run_on_site": "recovery",
                    "continue_on_failure": false
                }
            ]
        }
    ]
}
```

**Step Types**: `command`, `prompt`, `pause`

---

## Recovery Execution

### Start Recovery

**Endpoint**: `POST /api/recovery-plans/{rp-id}/recovery`

**Request**:

```json
{
    "recovery_type": "test",
    "sync_data": true,
    "recovery_options": {
        "power_on_vms": true,
        "run_scripts": true,
        "recovery_point_type": "latest"
    }
}
```

**Recovery Types**: `test`, `planned`, `disaster` (emergency)

**Recovery Point Types**: `latest`, `pit` (point-in-time), `specific`

**Response**:

```json
{
    "task_id": "task-12345",
    "recovery_type": "test",
    "state": "running",
    "start_time": "2024-01-15T14:30:00Z",
    "progress_percent": 0,
    "recovery_history_id": "rh-12345"
}
```

### Get Recovery Status

**Endpoint**: `GET /api/recovery-plans/{rp-id}/recovery`

**Response**:

```json
{
    "task_id": "task-12345",
    "recovery_type": "test",
    "state": "running",
    "progress_percent": 45,
    "current_step": "Powering on VMs in priority group 2",
    "start_time": "2024-01-15T14:30:00Z",
    "estimated_completion_time": "2024-01-15T14:50:00Z"
}
```

**Recovery States**: `not_started`, `running`, `prompting`, `paused`, `cancelling`, `completed`, `failed`

### Cancel Recovery

**Endpoint**: `POST /api/recovery-plans/{rp-id}/recovery/cancel`

### Answer Prompt

**Endpoint**: `POST /api/recovery-plans/{rp-id}/recovery/prompt`

**Request**:

```json
{
    "prompt_id": "prompt-001",
    "response": "continue"
}
```

**Prompt Responses**: `continue`, `skip`, `abort`

### Get Recovery History

**Endpoint**: `GET /api/recovery-plans/{rp-id}/recovery-history`

**Response**:

```json
{
    "list": [
        {
            "id": "rh-12345",
            "recovery_plan_id": "rp-12345",
            "recovery_plan_name": "WebApp-Recovery-Plan",
            "recovery_type": "test",
            "state": "completed",
            "result_state": "success",
            "start_time": "2024-01-15T14:30:00Z",
            "end_time": "2024-01-15T14:45:00Z",
            "duration_seconds": 900,
            "initiated_by": "administrator@vsphere.local",
            "vm_count": 15,
            "vms_succeeded": 15,
            "vms_failed": 0,
            "warnings_count": 2
        }
    ]
}
```

### Get Recovery History Details

**Endpoint**: `GET /api/recovery-plans/{rp-id}/recovery-history/{rh-id}`

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
    "recovery_priority_groups": [
        {
            "priority": 1,
            "name": "Database Tier",
            "state": "completed",
            "result_state": "success",
            "start_time": "2024-01-15T14:30:00Z",
            "end_time": "2024-01-15T14:35:00Z",
            "vm_recoveries": [
                {
                    "vm_id": "vm-001",
                    "vm_name": "db-server-01",
                    "state": "completed",
                    "result_state": "success",
                    "recovery_vm_id": "vm-recovery-001",
                    "power_state": "poweredOn",
                    "ip_address": "10.0.2.100",
                    "start_time": "2024-01-15T14:30:00Z",
                    "end_time": "2024-01-15T14:33:00Z",
                    "errors": [],
                    "warnings": []
                }
            ],
            "step_results": [
                {
                    "step_name": "Verify DB Health",
                    "step_type": "command",
                    "state": "completed",
                    "result_state": "success",
                    "output": "Database health check passed",
                    "duration_seconds": 45
                }
            ]
        }
    ],
    "errors": [],
    "warnings": [
        {
            "code": "WARN_001",
            "message": "VM web-server-03 took longer than expected to power on"
        }
    ]
}
```

### Cleanup Test Recovery

**Endpoint**: `POST /api/recovery-plans/{rp-id}/cleanup`

**Request**:

```json
{
    "recovery_history_id": "rh-12345",
    "force": false
}
```

---

## Reprotection and Failback

### Start Reprotection

**Endpoint**: `POST /api/recovery-plans/{rp-id}/reprotect`

**Purpose**: After a recovery, reprotect VMs to enable failback to the original site.

**Request**:

```json
{
    "recovery_history_id": "rh-12345",
    "options": {
        "reverse_replication": true,
        "sync_data": true
    }
}
```

### Get Reprotection Status

**Endpoint**: `GET /api/recovery-plans/{rp-id}/reprotect`

**Response**:

```json
{
    "task_id": "task-reprotect-001",
    "state": "running",
    "progress_percent": 60,
    "vms_reprotected": 10,
    "vms_total": 15,
    "current_vm": "app-server-05"
}
```

### Planned Failover (Failback)

**Endpoint**: `POST /api/recovery-plans/{rp-id}/planned-failover`

**Purpose**: Perform planned migration back to the original protected site.

**Request**:

```json
{
    "sync_data": true,
    "shutdown_source_vms": true,
    "options": {
        "power_on_vms": true,
        "run_scripts": true
    }
}
```

---

## Virtual Machine Management

### List Protected VMs

**Endpoint**: `GET /api/vms`

**Query Parameters**:

- `protection_group_id` - Filter by protection group
- `protection_state` - Filter by state
- `needs_configuration` - Filter VMs needing configuration

**Response**:

```json
{
    "list": [
        {
            "vm_id": "vm-001",
            "name": "web-server-01",
            "protection_group_id": "pg-12345",
            "protection_group_name": "WebServers-PG",
            "protection_state": "shadowing",
            "needs_configuration": false,
            "placeholder_vm_id": "vm-placeholder-001",
            "placeholder_vm_name": "web-server-01-placeholder",
            "replication_state": "synced",
            "rpo_violation": false,
            "last_sync_time": "2024-01-15T14:25:00Z"
        }
    ]
}
```

**Protection States**: `not_configured`, `configuring`, `shadowing`, `not_shadowing`, `error`

### Get VM Details

**Endpoint**: `GET /api/vms/{vm-id}`

**Response**:

```json
{
    "vm_id": "vm-001",
    "name": "web-server-01",
    "protection_group_id": "pg-12345",
    "protection_state": "shadowing",
    "placeholder_vm_id": "vm-placeholder-001",
    "source_site": {
        "site_id": "site-001",
        "vcenter": "vcenter-primary.example.com",
        "datacenter": "DC-Primary",
        "cluster": "Production-Cluster",
        "host": "esxi-host-01.example.com",
        "datastore": "WebServers-DS"
    },
    "recovery_site": {
        "site_id": "site-002",
        "vcenter": "vcenter-recovery.example.com",
        "datacenter": "DC-Recovery",
        "cluster": "DR-Cluster",
        "resource_pool": "DR-ResourcePool",
        "folder": "Recovered-VMs",
        "datastore": "DR-Datastore"
    },
    "recovery_settings": {
        "priority": "high",
        "startup_delay_seconds": 0,
        "shutdown_delay_seconds": 300,
        "skip_guest_shutdown": false,
        "power_on_after_recovery": true
    },
    "replication_info": {
        "replication_type": "san",
        "rpo_minutes": 15,
        "last_sync_time": "2024-01-15T14:25:00Z",
        "lag_seconds": 300,
        "state": "synced"
    }
}
```

### Configure VM Recovery Settings

**Endpoint**: `PUT /api/vms/{vm-id}/recovery-settings`

**Request**:

```json
{
    "priority": "high",
    "startup_delay_seconds": 60,
    "shutdown_delay_seconds": 300,
    "skip_guest_shutdown": false,
    "power_on_after_recovery": true,
    "depends_on_vms": ["vm-002"],
    "ip_customization": {
        "enabled": true,
        "rules": [
            {
                "nic_id": 0,
                "source_ip": "10.0.1.100",
                "target_ip": "10.0.2.100",
                "target_subnet_mask": "255.255.255.0",
                "target_gateway": "10.0.2.1",
                "target_dns_servers": ["10.0.2.10", "10.0.2.11"],
                "target_dns_suffix": "recovery.example.com"
            }
        ]
    },
    "pre_power_on_commands": [
        {
            "command": "/scripts/pre-start.sh",
            "timeout_seconds": 120,
            "run_in_guest": false
        }
    ],
    "post_power_on_commands": [
        {
            "command": "C:\\scripts\\post-start.bat",
            "timeout_seconds": 300,
            "run_in_guest": true,
            "guest_credentials": {
                "username": "administrator",
                "password_secret_id": "secret-001"
            }
        }
    ]
}
```

**VM Priority Values**: `lowest`, `low`, `normal`, `high`, `highest`

### Configure VM Network Mappings

**Endpoint**: `PUT /api/vms/{vm-id}/network-mappings`

**Request**:

```json
{
    "network_mappings": [
        {
            "source_network": "VM Network",
            "target_network": "DR-VM Network",
            "test_network": "Isolated-Test-Network"
        }
    ]
}
```

---

## Site Management

### List Sites

**Endpoint**: `GET /api/sites`

**Response**:

```json
{
    "list": [
        {
            "site_id": "site-001",
            "name": "Primary-Site",
            "type": "protected",
            "state": "connected",
            "vcenter_server": "vcenter-primary.example.com",
            "srm_server": "srm-primary.example.com",
            "srm_version": "8.6.0",
            "vcenter_version": "8.0.1"
        },
        {
            "site_id": "site-002",
            "name": "Recovery-Site",
            "type": "recovery",
            "state": "connected",
            "vcenter_server": "vcenter-recovery.example.com",
            "srm_server": "srm-recovery.example.com",
            "srm_version": "8.6.0",
            "vcenter_version": "8.0.1"
        }
    ]
}
```

**Site Types**: `protected`, `recovery`

**Site States**: `connected`, `disconnected`, `partially_connected`

### Get Site Pairing Status

**Endpoint**: `GET /api/sites/{site-id}/pairing`

**Response**:

```json
{
    "local_site_id": "site-001",
    "local_site_name": "Primary-Site",
    "remote_site_id": "site-002",
    "remote_site_name": "Recovery-Site",
    "pairing_state": "paired",
    "connection_state": "connected",
    "last_heartbeat": "2024-01-15T14:30:00Z",
    "replication_health": "healthy",
    "array_managers": [
        {
            "id": "am-001",
            "name": "NetApp-SRA",
            "type": "san",
            "state": "connected",
            "replicated_devices": 10
        }
    ],
    "vr_servers": [
        {
            "id": "vr-001",
            "name": "vSphere-Replication-Server",
            "state": "connected",
            "replicated_vms": 25
        }
    ]
}
```

### Get Site Summary

**Endpoint**: `GET /api/sites/{site-id}/summary`

**Response**:

```json
{
    "site_id": "site-001",
    "protection_groups_count": 5,
    "recovery_plans_count": 3,
    "protected_vms_count": 50,
    "placeholder_vms_count": 50,
    "last_test_date": "2024-01-10T14:00:00Z",
    "rpo_violations_count": 0,
    "issues_count": 2
}
```

---

## Inventory Management

### List Datastores

**Endpoint**: `GET /api/inventory/datastores`

**Query Parameters**:

- `site_id` - Filter by site
- `replication_state` - Filter by replication state

**Response**:

```json
{
    "list": [
        {
            "datastore_id": "ds-001",
            "name": "WebServers-DS",
            "type": "vmfs",
            "capacity_bytes": 536870912000,
            "free_bytes": 268435456000,
            "protection_group_id": "pg-12345",
            "replication_state": "synced",
            "array_manager": "NetApp-SRA",
            "replicated_device_id": "lun-001"
        }
    ]
}
```

### List Networks

**Endpoint**: `GET /api/inventory/networks`

**Response**:

```json
{
    "list": [
        {
            "network_id": "network-001",
            "name": "VM Network",
            "type": "standard",
            "vlan_id": 100,
            "site_id": "site-001"
        },
        {
            "network_id": "network-002",
            "name": "Production-DVS",
            "type": "distributed",
            "vlan_id": 200,
            "site_id": "site-001"
        }
    ]
}
```

### List Resource Pools

**Endpoint**: `GET /api/inventory/resource-pools`

**Response**:

```json
{
    "list": [
        {
            "resource_pool_id": "rp-001",
            "name": "Production-RP",
            "cluster": "Production-Cluster",
            "cpu_limit_mhz": 10000,
            "cpu_reservation_mhz": 5000,
            "memory_limit_mb": 32768,
            "memory_reservation_mb": 16384,
            "vm_count": 15,
            "site_id": "site-001"
        }
    ]
}
```

### List Folders

**Endpoint**: `GET /api/inventory/folders`

**Response**:

```json
{
    "list": [
        {
            "folder_id": "folder-001",
            "name": "Production-VMs",
            "path": "/DC-Primary/vm/Production-VMs",
            "type": "vm",
            "site_id": "site-001"
        }
    ]
}
```

### Get Inventory Mappings

**Endpoint**: `GET /api/inventory/mappings`

**Response**:

```json
{
    "network_mappings": [
        {
            "id": "nm-001",
            "source_network": "VM Network",
            "target_network": "DR-VM Network",
            "test_network": "Isolated-Test-Network"
        }
    ],
    "folder_mappings": [
        {
            "id": "fm-001",
            "source_folder": "Production-VMs",
            "target_folder": "Recovered-VMs"
        }
    ],
    "resource_mappings": [
        {
            "id": "rm-001",
            "source_resource": "Production-Cluster",
            "target_resource": "DR-Cluster"
        }
    ]
}
```

---

## Tasks and Async Operations

### List Tasks

**Endpoint**: `GET /api/tasks`

**Query Parameters**:

- `state` - Filter by task state
- `type` - Filter by task type
- `start_time_after` - Filter by start time

**Response**:

```json
{
    "list": [
        {
            "task_id": "task-12345",
            "name": "Test Recovery - WebApp-Recovery-Plan",
            "type": "recovery",
            "state": "running",
            "progress_percent": 45,
            "start_time": "2024-01-15T14:30:00Z",
            "initiated_by": "administrator@vsphere.local",
            "target_id": "rp-12345",
            "target_type": "recovery_plan"
        }
    ]
}
```

**Task States**: `queued`, `running`, `completed`, `failed`, `cancelled`

**Task Types**: `recovery`, `cleanup`, `reprotect`, `planned_failover`, `protection_group_create`, `protection_group_delete`

### Get Task Details

**Endpoint**: `GET /api/tasks/{task-id}`

**Response**:

```json
{
    "task_id": "task-12345",
    "name": "Test Recovery - WebApp-Recovery-Plan",
    "type": "recovery",
    "state": "running",
    "progress_percent": 45,
    "start_time": "2024-01-15T14:30:00Z",
    "current_step": "Powering on VMs in priority group 2",
    "steps": [
        {
            "step_number": 1,
            "name": "Prepare recovery",
            "state": "completed",
            "duration_seconds": 30
        },
        {
            "step_number": 2,
            "name": "Power on priority group 1",
            "state": "completed",
            "duration_seconds": 180
        },
        {
            "step_number": 3,
            "name": "Power on priority group 2",
            "state": "running",
            "progress_percent": 60
        }
    ],
    "errors": [],
    "warnings": []
}
```

### Cancel Task

**Endpoint**: `POST /api/tasks/{task-id}/cancel`

---

## Compliance and Reporting

### Get Recovery Plan Test History

**Endpoint**: `GET /api/recovery-plans/{rp-id}/test-history`

**Response**:

```json
{
    "list": [
        {
            "test_id": "test-001",
            "test_date": "2024-01-10T14:00:00Z",
            "result": "success",
            "duration_seconds": 900,
            "vms_recovered": 15,
            "vms_failed": 0,
            "rpo_achieved_seconds": 300,
            "rto_achieved_seconds": 900,
            "initiated_by": "administrator@vsphere.local",
            "notes": "Quarterly DR test"
        }
    ]
}
```

### Generate Compliance Report

**Endpoint**: `POST /api/reports/compliance`

**Request**:

```json
{
    "report_type": "rpo_rto_compliance",
    "date_range": {
        "start_date": "2024-01-01T00:00:00Z",
        "end_date": "2024-01-31T23:59:59Z"
    },
    "recovery_plans": ["rp-12345", "rp-12346"],
    "format": "pdf"
}
```

**Report Types**: `rpo_rto_compliance`, `test_history`, `protection_status`, `recovery_readiness`

**Response**:

```json
{
    "report_id": "report-001",
    "state": "generating",
    "download_url": null
}
```

### Get Report Status

**Endpoint**: `GET /api/reports/{report-id}`

**Response**:

```json
{
    "report_id": "report-001",
    "report_type": "rpo_rto_compliance",
    "state": "completed",
    "generated_time": "2024-01-15T15:00:00Z",
    "download_url": "https://srm-server/api/reports/report-001/download",
    "expires_time": "2024-01-16T15:00:00Z"
}
```

### Get RPO Violations

**Endpoint**: `GET /api/reports/rpo-violations`

**Response**:

```json
{
    "list": [
        {
            "vm_id": "vm-010",
            "vm_name": "app-server-10",
            "protection_group": "AppServers-PG",
            "configured_rpo_minutes": 15,
            "current_lag_minutes": 45,
            "violation_start_time": "2024-01-15T13:00:00Z",
            "cause": "Network connectivity issue"
        }
    ],
    "total_violations": 1
}
```

---

## Error Handling

### Common Error Responses

| Error Type | HTTP Status | Description |
|------------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Operation conflicts with current state |
| `PRECONDITION_FAILED` | 412 | Precondition not met |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

**Example Error Response**:

```json
{
    "error_type": "CONFLICT",
    "message": "Cannot start recovery while test is in progress",
    "details": {
        "current_state": "test_running",
        "recovery_plan_id": "rp-12345",
        "active_task_id": "task-12345"
    },
    "timestamp": "2024-01-15T14:30:00Z",
    "request_id": "req-abc123"
}
```

**Validation Error**:

```json
{
    "error_type": "INVALID_REQUEST",
    "message": "Validation failed",
    "details": {
        "field_errors": [
            {
                "field": "name",
                "message": "Protection group name already exists"
            },
            {
                "field": "datastores",
                "message": "At least one datastore is required"
            }
        ]
    }
}
```

---

## PowerCLI Integration Examples

### Connect to SRM

```powershell
# Connect to vCenter and SRM
Connect-VIServer -Server vcenter.example.com -User admin -Password $password
$srmConnection = Connect-SrmServer -SrmServer srm.example.com -RemoteUser admin

# Get SRM API object
$srmApi = $srmConnection.ExtensionData
```

### List Protection Groups (PowerCLI)

```powershell
# Get all protection groups
$protectionGroups = Get-ProtectionGroup

# Get protection group details
foreach ($pg in $protectionGroups) {
    Write-Host "Protection Group: $($pg.Name)"
    Write-Host "  State: $($pg.State)"
    Write-Host "  VM Count: $($pg.GetProtectedVms().Count)"
}
```

### Execute Recovery Plan

```powershell
# Get recovery plan
$recoveryPlan = Get-RecoveryPlan -Name "WebApp-Recovery-Plan"

# Start test recovery
$testTask = Start-RecoveryPlan -RecoveryPlan $recoveryPlan -RecoveryMode Test -SyncData

# Monitor progress
do {
    Start-Sleep -Seconds 30
    $task = Get-SrmTask -Task $testTask
    Write-Host "Progress: $($task.PercentComplete)% - $($task.State)"
} while ($task.State -eq "Running")

# Check result
if ($task.State -eq "Success") {
    Write-Host "Test recovery completed successfully"
    
    # Cleanup test
    Stop-RecoveryPlan -RecoveryPlan $recoveryPlan -CleanupTest
} else {
    Write-Host "Test recovery failed: $($task.Error)"
}
```

### Configure VM Recovery Settings (PowerCLI)

```powershell
# Get protected VM
$vm = Get-ProtectedVm -Name "web-server-01"

# Configure recovery settings
$recoverySettings = @{
    Priority = "High"
    StartupDelaySeconds = 60
    ShutdownDelaySeconds = 300
}

Set-ProtectedVm -ProtectedVm $vm -RecoverySettings $recoverySettings

# Configure IP customization
$ipMapping = @{
    SourceIp = "10.0.1.100"
    TargetIp = "10.0.2.100"
    TargetSubnetMask = "255.255.255.0"
    TargetGateway = "10.0.2.1"
}

Set-ProtectedVm -ProtectedVm $vm -IpCustomization $ipMapping
```

### Reprotection After Recovery

```powershell
# Get recovery plan after successful recovery
$recoveryPlan = Get-RecoveryPlan -Name "WebApp-Recovery-Plan"

# Start reprotection
$reprotectTask = Start-SrmReprotect -RecoveryPlan $recoveryPlan

# Monitor reprotection
do {
    Start-Sleep -Seconds 60
    $task = Get-SrmTask -Task $reprotectTask
    Write-Host "Reprotection Progress: $($task.PercentComplete)%"
} while ($task.State -eq "Running")

Write-Host "Reprotection completed: $($task.State)"
```

---

## Python SDK Examples

### REST API Client Setup

```python
import requests
import base64
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings for self-signed certs (not recommended for production)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class SrmClient:
    def __init__(self, srm_server, username, password):
        self.base_url = f"https://{srm_server}/api"
        self.session = requests.Session()
        self.session.verify = False  # Use True with valid certs
        self._authenticate(username, password)
    
    def _authenticate(self, username, password):
        """Authenticate and get session token"""
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        response = self.session.post(
            f"{self.base_url}/sessions",
            headers={"Authorization": f"Basic {credentials}"}
        )
        response.raise_for_status()
        self.session_id = response.json()["session_id"]
        self.session.headers["vmware-api-session-id"] = self.session_id
    
    def get_protection_groups(self):
        """List all protection groups"""
        response = self.session.get(f"{self.base_url}/protection-groups")
        response.raise_for_status()
        return response.json()["list"]
    
    def get_recovery_plans(self):
        """List all recovery plans"""
        response = self.session.get(f"{self.base_url}/recovery-plans")
        response.raise_for_status()
        return response.json()["list"]
    
    def start_test_recovery(self, recovery_plan_id, sync_data=True):
        """Start a test recovery"""
        payload = {
            "recovery_type": "test",
            "sync_data": sync_data,
            "recovery_options": {
                "power_on_vms": True,
                "run_scripts": True
            }
        }
        response = self.session.post(
            f"{self.base_url}/recovery-plans/{recovery_plan_id}/recovery",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def get_recovery_status(self, recovery_plan_id):
        """Get current recovery status"""
        response = self.session.get(
            f"{self.base_url}/recovery-plans/{recovery_plan_id}/recovery"
        )
        response.raise_for_status()
        return response.json()
    
    def cleanup_test(self, recovery_plan_id, recovery_history_id):
        """Cleanup test recovery"""
        payload = {"recovery_history_id": recovery_history_id}
        response = self.session.post(
            f"{self.base_url}/recovery-plans/{recovery_plan_id}/cleanup",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def logout(self):
        """End session"""
        self.session.delete(f"{self.base_url}/sessions")
```

### Complete Test Recovery Workflow

```python
import time

def execute_test_recovery(srm_client, recovery_plan_name):
    """Execute a complete test recovery workflow"""
    
    # Find recovery plan
    plans = srm_client.get_recovery_plans()
    plan = next((p for p in plans if p["name"] == recovery_plan_name), None)
    
    if not plan:
        raise ValueError(f"Recovery plan '{recovery_plan_name}' not found")
    
    plan_id = plan["id"]
    print(f"Starting test recovery for: {plan['name']}")
    
    # Start test recovery
    result = srm_client.start_test_recovery(plan_id)
    recovery_history_id = result["recovery_history_id"]
    print(f"Recovery started: {result['task_id']}")
    
    # Monitor progress
    while True:
        status = srm_client.get_recovery_status(plan_id)
        print(f"Progress: {status['progress_percent']}% - {status.get('current_step', 'N/A')}")
        
        if status["state"] in ["completed", "failed"]:
            break
        
        time.sleep(30)
    
    # Check result
    if status["state"] == "completed":
        print("Test recovery completed successfully!")
        
        # Cleanup
        print("Starting cleanup...")
        srm_client.cleanup_test(plan_id, recovery_history_id)
        print("Cleanup completed")
        return True
    else:
        print(f"Test recovery failed: {status.get('errors', [])}")
        return False

# Usage
if __name__ == "__main__":
    client = SrmClient("srm.example.com", "admin@vsphere.local", "password")
    try:
        execute_test_recovery(client, "WebApp-Recovery-Plan")
    finally:
        client.logout()
```

---

## Best Practices

### API Usage Guidelines

1. **Session Management**: Maintain active sessions and implement automatic re-authentication on session expiry.

2. **Polling Intervals**: Use appropriate intervals for monitoring operations (30-60 seconds for recovery, 5-10 seconds for quick operations).

3. **Error Handling**: Implement retry logic with exponential backoff for transient failures.

4. **Concurrent Operations**: Respect SRM's limits on concurrent operations per recovery plan.

5. **State Validation**: Always check resource states before starting operations.

6. **Idempotency**: Design automation to handle partial failures and be safely re-runnable.

### Recovery Plan Design

1. **Priority Groups**: Use priority groups for dependency management between application tiers.

2. **Startup Delays**: Configure appropriate delays between VM startups to avoid resource contention.

3. **Network Customization**: Plan IP address schemes for recovery site to avoid conflicts.

4. **Testing Schedule**: Implement regular automated testing (monthly recommended).

5. **Documentation**: Maintain runbooks for manual intervention scenarios.

6. **Callout Scripts**: Use pre/post power-on scripts for application-specific recovery steps.

### Comparison: Generic DR Patterns vs AWS DRS

| Feature | Traditional DR Solutions | AWS DRS |
|---------|--------------------------|---------|
| Protection Unit | Protection Group (storage/resources) | Source Server |
| Recovery Unit | Recovery Plan | Recovery Job |
| Replication | Various (SAN/agent/snapshot) | Agent-based continuous replication |
| Recovery Types | Test, Planned, Emergency | Drill, Recovery |
| Failback | Platform-specific reprotection | Reverse replication |
| Orchestration | Priority groups with scripts | Wave-based execution |
| Network Customization | IP mapping rules | Launch template settings |
| API Style | REST with session auth | AWS Signature V4 |
| Automation | Platform-specific SDKs | boto3, AWS CLI |

---

## Rate Limits and Quotas

| Operation | Limit |
|-----------|-------|
| Concurrent recovery operations | 1 per recovery plan |
| Concurrent test recoveries | 1 per site pair |
| API requests per minute | 100 |
| Maximum VMs per protection group | 500 |
| Maximum protection groups per recovery plan | 50 |
| Maximum recovery plans per site | 250 |

---

## Related Resources

- [VMware SRM Documentation](https://docs.vmware.com/en/Site-Recovery-Manager/index.html)
- [VMware SRM API Reference](https://developer.vmware.com/apis/1196/site-recovery-manager)
- [PowerCLI SRM Cmdlets](https://developer.vmware.com/docs/powercli/latest/products/siterecoverymanager/)
- [vSphere Replication Documentation](https://docs.vmware.com/en/vSphere-Replication/index.html)
- [VMware Cloud DR Documentation](https://docs.vmware.com/en/VMware-Cloud-Disaster-Recovery/index.html)

---

## Glossary

| Term | Definition |
|------|------------|
| Protection Group | Collection of VMs or datastores protected together |
| Recovery Plan | Orchestration definition for recovering protection groups |
| Placeholder VM | Skeleton VM at recovery site representing protected VM |
| Shadowing | Active replication state where data is being replicated |
| Reprotection | Process of reversing protection direction after recovery |
| RPO | Recovery Point Objective - maximum acceptable data loss |
| RTO | Recovery Time Objective - maximum acceptable downtime |
| SRA | Storage Replication Adapter - plugin for array-based replication |
| vSphere Replication | Host-based replication technology |
