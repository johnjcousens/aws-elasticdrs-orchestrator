# Requirements Document

## Introduction

This feature enables complete disaster recovery lifecycle management through automated failover and failback orchestration. After a failover to a recovery region, the system automatically installs DRS agents on recovery instances, creates mirrored Protection Groups and Recovery Plans with original region network settings, monitors reverse replication progress, and orchestrates failback to the source region.

## Glossary

- **Failover Session**: A tracked session representing a completed failover event, including recovery instances and their states
- **Reverse Replication**: The process of replicating data from recovery instances back to the source region
- **Configuration Mirroring**: Automatic creation of Protection Groups and Recovery Plans in the recovery region that target the original source region
- **Failback**: The process of launching instances in the source region from reverse-replicated data
- **Re-protection**: Establishing forward replication from failback instances to the recovery region

## Requirements

### Requirement 1: Failover Session Tracking

**User Story:** As a DR administrator, I want the system to automatically track completed failover events, so that I can manage the failback process from a centralized view.

#### Acceptance Criteria

1. WHEN an execution completes with `executionType: RECOVERY` THEN the System SHALL automatically create a Failover Session record
2. WHEN creating a Failover Session THEN the System SHALL query DRS for all recovery instances from the execution
3. WHEN creating a Failover Session THEN the System SHALL store the source region, recovery region, and original Protection Group/Recovery Plan references
4. WHEN a user requests the list of Failover Sessions THEN the System SHALL return all sessions with their current status
5. WHEN a user requests a specific Failover Session THEN the System SHALL return complete details including all recovery instances and their states

### Requirement 2: DRS Agent Installation on Recovery Instances

**User Story:** As a DR administrator, I want to install DRS agents on recovery instances via the UI, so that I can enable reverse replication without manual SSH access.

#### Technical Notes

**Agent Uninstallation (Required Before Reinstall)**

Recovery instances from DRS already have the agent installed pointing to the original region. Before installing the agent for reverse replication, the existing agent must be uninstalled:

- **Windows**: `C:\Program Files (x86)\AWS Replication Agent\uninstall_agent_windows.bat`
- **Linux**: `/var/lib/aws-replication-agent/uninstall_agent_linux.sh`

The agent cannot be reinstalled to point to a different region/account without first uninstalling. Attempting to do so results in error: *"Cannot install agent, as this server was previously installed to replicate into another region or account."*

**SSM Commands for Agent Lifecycle**:
```powershell
# Windows - Stop, Uninstall, Reboot
& "C:\Program Files (x86)\AWS Replication Agent\stopAgent.bat"
& "C:\Program Files (x86)\AWS Replication Agent\uninstall_agent_windows.bat"
Remove-Item -Path "C:\Program Files (x86)\AWS Replication Agent" -Recurse -Force
Restart-Computer -Force
```

```bash
# Linux - Stop, Uninstall, Reboot
sudo /var/lib/aws-replication-agent/stopAgent.sh
sudo /var/lib/aws-replication-agent/uninstall_agent_linux.sh
sudo rm -rf /var/lib/aws-replication-agent
sudo reboot
```

#### Acceptance Criteria

1. WHEN a user initiates agent installation for a Failover Session THEN the System SHALL verify all recovery instances have SSM agent running
2. WHEN SSM agent is running THEN the System SHALL first uninstall any existing DRS agent using the platform-specific uninstall script
3. WHEN uninstalling the existing agent THEN the System SHALL reboot the instance and wait for SSM connectivity
4. WHEN the instance is ready THEN the System SHALL execute the `AWSDisasterRecovery-InstallDRAgentOnInstance` SSM document
5. WHEN executing the SSM document THEN the System SHALL pass the source region as the target for reverse replication
6. WHEN agent installation is in progress THEN the System SHALL update the session status to `INSTALLING_AGENTS`
7. WHEN a user requests agent installation status THEN the System SHALL return the SSM command status for each instance
8. IF agent installation fails on any instance THEN the System SHALL report the specific failure reason and allow retry
9. WHEN agent installation completes successfully THEN the System SHALL verify new source servers are created in the source region

### Requirement 3: Automatic Protection Group Mirroring

**User Story:** As a DR administrator, I want the system to automatically create mirrored Protection Groups for failback, so that I don't have to manually recreate configurations.

#### Acceptance Criteria

1. WHEN agent installation completes THEN the System SHALL map original source servers to newly created source servers via hostname/tags
2. WHEN creating a mirrored Protection Group THEN the System SHALL use the original Protection Group's launch configuration
3. WHEN creating a mirrored Protection Group THEN the System SHALL preserve the original region's subnet ID from the launch config
4. WHEN creating a mirrored Protection Group THEN the System SHALL preserve the original region's security group IDs from the launch config
5. WHEN creating a mirrored Protection Group THEN the System SHALL preserve the original region's instance profile ARN from the launch config
6. WHEN creating a mirrored Protection Group THEN the System SHALL preserve instance type, copy private IP, and copy tags settings
7. WHEN a mirrored Protection Group is created THEN the System SHALL apply the launch settings to the DRS source servers via API
8. WHEN mirroring completes THEN the System SHALL update the Failover Session with mirrored Protection Group IDs

### Requirement 4: Automatic Recovery Plan Mirroring

**User Story:** As a DR administrator, I want the system to automatically create a mirrored Recovery Plan for failback, so that wave configurations and dependencies are preserved.

#### Acceptance Criteria

1. WHEN Protection Group mirroring completes THEN the System SHALL create a mirrored Recovery Plan
2. WHEN creating a mirrored Recovery Plan THEN the System SHALL map original Protection Group IDs to mirrored Protection Group IDs in each wave
3. WHEN creating a mirrored Recovery Plan THEN the System SHALL preserve wave numbers, dependencies, and pause settings
4. WHEN creating a mirrored Recovery Plan THEN the System SHALL preserve pre-wave and post-wave SSM actions
5. WHEN the mirrored Recovery Plan is created THEN the System SHALL update the Failover Session status to `CONFIG_MIRRORED`
6. WHEN mirroring completes THEN the System SHALL update the Failover Session with the mirrored Recovery Plan ID

### Requirement 5: Reverse Replication Management

**User Story:** As a DR administrator, I want to start and monitor reverse replication from the UI, so that I can track when the system is ready for failback.

#### Acceptance Criteria

1. WHEN a user initiates reverse replication THEN the System SHALL call the DRS API to start reverse replication for each recovery instance
2. WHEN reverse replication is started THEN the System SHALL update the session status to `REVERSE_REPLICATING`
3. WHEN reverse replication is in progress THEN the System SHALL poll DRS every 60 seconds for status updates
4. WHEN polling reverse replication status THEN the System SHALL track each instance's state: NOT_STARTED, INITIATING, INITIAL_SYNC, CONTINUOUS, READY, READY_WITH_LAG, ERROR
5. WHEN all instances reach READY or READY_WITH_LAG state THEN the System SHALL update the session status to `READY_FOR_FAILBACK`
6. WHEN any instance enters ERROR state THEN the System SHALL report the error and allow retry
7. WHEN a user requests reverse replication status THEN the System SHALL return the current state for each recovery instance

### Requirement 6: Failback Execution

**User Story:** As a DR administrator, I want to execute failback with one click using the mirrored configuration, so that I can quickly restore services to the source region.

#### Acceptance Criteria

1. WHEN a Failover Session is in `READY_FOR_FAILBACK` status THEN the System SHALL enable the Execute Failback action
2. WHEN a user initiates failback THEN the System SHALL allow selection of Drill or Recovery mode
3. WHEN executing failback THEN the System SHALL create an execution using the mirrored Recovery Plan
4. WHEN failback execution starts THEN the System SHALL update the session status to `FAILBACK_IN_PROGRESS`
5. WHEN failback execution completes successfully THEN the System SHALL update the session status to `FAILBACK_COMPLETE`
6. IF failback execution fails THEN the System SHALL report the failure and allow retry

### Requirement 7: Re-protection After Failback

**User Story:** As a DR administrator, I want to re-protect failback instances, so that they are protected for future DR events.

#### Acceptance Criteria

1. WHEN failback completes successfully THEN the System SHALL enable the Re-protect action
2. WHEN a user initiates re-protection THEN the System SHALL start forward replication from failback instances to the recovery region
3. WHEN re-protection is initiated THEN the System SHALL update the original source servers in DRS
4. WHEN re-protection completes THEN the System SHALL update the session status to `RE_PROTECTED`

### Requirement 8: Recovery Region Cleanup

**User Story:** As a DR administrator, I want to clean up recovery region resources after failback, so that I don't incur unnecessary costs.

#### Acceptance Criteria

1. WHEN failback completes successfully THEN the System SHALL enable the Cleanup action
2. WHEN a user initiates cleanup THEN the System SHALL display a confirmation with resources to be deleted
3. WHEN cleanup is confirmed THEN the System SHALL terminate recovery instances in the recovery region
4. WHEN cleanup is confirmed THEN the System SHALL delete mirrored Protection Groups from DynamoDB
5. WHEN cleanup is confirmed THEN the System SHALL delete the mirrored Recovery Plan from DynamoDB
6. WHEN cleanup is confirmed THEN the System SHALL optionally delete source servers from DRS in the recovery region
7. WHEN cleanup completes THEN the System SHALL update the session status to `CLEANUP_COMPLETE`

### Requirement 9: Failover Sessions UI

**User Story:** As a DR administrator, I want a dedicated UI page for managing Failover Sessions, so that I can easily track and manage the failback process.

#### Acceptance Criteria

1. WHEN a user navigates to Failover Sessions THEN the System SHALL display a table of all sessions with status, regions, and instance counts
2. WHEN a user clicks on a session THEN the System SHALL display detailed information including all recovery instances
3. WHEN viewing a session THEN the System SHALL display available actions based on current status
4. WHEN viewing a session THEN the System SHALL display links to the original and mirrored Protection Groups and Recovery Plans
5. WHEN viewing a session THEN the System SHALL display reverse replication progress for each instance

### Requirement 10: Failback Wizard

**User Story:** As a DR administrator, I want a step-by-step wizard for failback preparation, so that I can ensure all prerequisites are met before executing failback.

#### Acceptance Criteria

1. WHEN a user opens the Failback Wizard THEN the System SHALL display a multi-step workflow
2. WHEN on Step 1 (Review) THEN the System SHALL display all recovery instances and their current state
3. WHEN on Step 2 (Install Agents) THEN the System SHALL allow initiating agent installation and show progress
4. WHEN on Step 3 (Mirror Config) THEN the System SHALL allow initiating configuration mirroring and show results
5. WHEN on Step 4 (Reverse Replication) THEN the System SHALL allow starting reverse replication and show progress
6. WHEN on Step 5 (Monitor) THEN the System SHALL display real-time reverse replication status
7. WHEN on Step 6 (Execute) THEN the System SHALL allow executing failback when ready
8. WHEN any step fails THEN the System SHALL display error details and allow retry without losing progress

### Requirement 11: API Endpoints

**User Story:** As a developer, I want comprehensive API endpoints for failover/failback operations, so that I can automate DR workflows.

#### Acceptance Criteria

1. WHEN calling `GET /failover-sessions` THEN the System SHALL return all Failover Sessions
2. WHEN calling `GET /failover-sessions/{id}` THEN the System SHALL return complete session details
3. WHEN calling `POST /failover-sessions/{id}/install-agents` THEN the System SHALL initiate agent installation
4. WHEN calling `GET /failover-sessions/{id}/agent-status` THEN the System SHALL return installation status
5. WHEN calling `POST /failover-sessions/{id}/mirror-config` THEN the System SHALL create mirrored PGs and RP
6. WHEN calling `POST /failover-sessions/{id}/start-reverse-replication` THEN the System SHALL start reverse replication
7. WHEN calling `GET /failover-sessions/{id}/reverse-replication-status` THEN the System SHALL return replication status
8. WHEN calling `POST /failover-sessions/{id}/execute-failback` THEN the System SHALL execute failback
9. WHEN calling `POST /failover-sessions/{id}/re-protect` THEN the System SHALL initiate re-protection
10. WHEN calling `POST /failover-sessions/{id}/cleanup` THEN the System SHALL clean up recovery region resources

### Requirement 12: Error Handling and Logging

**User Story:** As a developer, I want comprehensive error handling and logging, so that I can troubleshoot failback issues.

#### Acceptance Criteria

1. WHEN any failback operation fails THEN the System SHALL log the operation, session ID, and detailed error to CloudWatch
2. WHEN agent installation fails THEN the System SHALL include the SSM command output in the error response
3. WHEN server mapping fails THEN the System SHALL report which servers could not be mapped and why
4. WHEN reverse replication fails THEN the System SHALL include the DRS error message
5. WHEN any operation fails THEN the System SHALL update the session with the error details for UI display
6. WHEN retrying a failed operation THEN the System SHALL log the retry attempt with correlation ID
