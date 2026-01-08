# Technology Adapters

[← Back to Index](./README.md) | [← Previous: API Integration](./03-api-integration.md)

---

This document describes the technology adapter architecture that enables the Enterprise DR Orchestration Platform to integrate with multiple DR technologies through a standardized interface.

---

## Table of Contents

- [Adapter Architecture Pattern](#adapter-architecture-pattern)
- [Standard Adapter Interface](#standard-adapter-interface)
- [DRS Adapter](#drs-adapter)
- [Database Adapter](#database-adapter)
- [Application Adapter](#application-adapter)
- [Infrastructure Adapter](#infrastructure-adapter)
- [SQL Always On Adapter](#sql-always-on-adapter)
- [NetApp ONTAP Adapter](#netapp-ontap-adapter)
- [S3 Cross-Region Adapter](#s3-cross-region-adapter)

---

## Adapter Architecture Pattern

Each technology adapter follows a standardized interface pattern that integrates seamlessly with the Step Functions orchestration engine:

```mermaid
flowchart TD
    subgraph "🎯 Master Orchestration"
        MASTER[Master Step Functions]
        WAVE[Wave Controller]
    end
    
    subgraph "🔌 Technology Adapters"
        DRS[DRS Adapter]
        DB[Database Adapter]
        APP[Application Adapter]
        INFRA[Infrastructure Adapter]
        SQL[SQL Always On]
        ONTAP[NetApp ONTAP]
        S3[S3 Cross-Region]
    end

    subgraph "☁️ AWS Services"
        AWS_DRS[AWS DRS]
        RDS[RDS/Aurora]
        EC2[EC2/SSM]
        R53[Route 53]
        ELB[Load Balancers]
    end
    
    MASTER --> WAVE
    WAVE --> DRS
    WAVE --> DB
    WAVE --> APP
    WAVE --> INFRA
    WAVE --> SQL
    WAVE --> ONTAP
    WAVE --> S3
    
    DRS --> AWS_DRS
    DB --> RDS
    APP --> EC2
    INFRA --> R53
    INFRA --> ELB
    
    classDef orchestration fill:#4CAF50,stroke:#2E7D32,color:#fff
    classDef adapter fill:#2196F3,stroke:#1565C0,color:#fff
    classDef aws fill:#FF9800,stroke:#E65100,color:#fff
    
    class MASTER,WAVE orchestration
    class DRS,DB,APP,INFRA,SQL,ONTAP,S3 adapter
    class AWS_DRS,RDS,EC2,R53,ELB aws
```

---

## Standard Adapter Interface

All technology adapters implement a standardized interface for consistent orchestration:

```python
class TechnologyAdapter:
    """Base interface for all technology adapters."""
    
    def __init__(self, technology_type: str, config: dict):
        self.technology_type = technology_type
        self.config = config
        self.task_token = None
    
    def execute(self, task_token: str, resources: list, wave_config: dict) -> dict:
        """Standard execution interface for all technology adapters."""
        self.task_token = task_token
        
        try:
            # 1. Validate resources and configuration
            validated_resources = self.validate_resources(resources)
            
            # 2. Execute technology-specific operations
            execution_id = self.start_execution(validated_resources, wave_config)
            
            # 3. Monitor execution progress
            self.monitor_execution(execution_id)
            
            # 4. Generate standardized results
            results = self.generate_results(execution_id)
            
            # 5. Send success callback to Step Functions
            self.send_task_success(results)
            
            return results
            
        except Exception as e:
            self.send_task_failure(str(e))
            raise
    
    def validate_resources(self, resources: list) -> list:
        """Technology-specific resource validation."""
        raise NotImplementedError
    
    def start_execution(self, resources: list, config: dict) -> str:
        """Start technology-specific execution."""
        raise NotImplementedError
    
    def monitor_execution(self, execution_id: str) -> None:
        """Monitor execution until completion."""
        raise NotImplementedError
    
    def generate_results(self, execution_id: str) -> dict:
        """Generate standardized results format."""
        raise NotImplementedError
```

### Adapter Result Format

All adapters return results in a standardized format:

```json
{
  "executionId": "adapter-exec-12345",
  "technology": "drs|database|application|infrastructure",
  "status": "completed|failed|cancelled",
  "results": {
    "processedResources": ["resource-1", "resource-2"],
    "executionTime": "PT15M30S",
    "nextPhaseReady": true,
    "validationRequired": false,
    "technologySpecificData": {}
  }
}
```

---

## DRS Adapter

The DRS Adapter integrates the existing DRS Orchestration solution as the core DRS technology component.

### Integration Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **API** | Call DRS solution REST API | Standard integration |
| **Step Functions** | Direct Step Functions invocation | Low-latency requirements |

### DRS Adapter Implementation

```python
class DRSAdapter(TechnologyAdapter):
    """DRS technology adapter leveraging existing DRS solution."""
    
    def __init__(self, config: dict):
        super().__init__("drs", config)
        self.drs_api_endpoint = config["drs_api_endpoint"]
        self.drs_step_function_arn = config.get("drs_step_function_arn")
        self.integration_mode = config.get("integration_mode", "api")
    
    def validate_resources(self, resources: dict) -> dict:
        """Validate DRS resources using existing DRS solution."""
        response = requests.post(
            f"{self.drs_api_endpoint}/validation/resources",
            json={"resources": resources, "validationType": "pre_execution"},
            headers=self._get_auth_headers()
        )
        return response.json()
    
    def start_execution(self, resources: dict, config: dict) -> str:
        """Execute DRS recovery using existing solution."""
        drs_request = {
            "recoveryPlanId": resources.get("recoveryPlanId"),
            "executionType": config.get("executionType", "RECOVERY"),
            "initiatedBy": "Enterprise-DR-Platform",
            "enterpriseContext": {
                "parentExecutionId": resources.get("parentExecutionId"),
                "waveNumber": resources.get("waveNumber")
            },
            "protectionGroups": resources.get("protectionGroups", []),
            "sourceServers": resources.get("sourceServers", [])
        }
        
        if self.integration_mode == "step_functions":
            return self._start_drs_step_function(drs_request)
        else:
            return self._start_drs_api_execution(drs_request)
    
    def _start_drs_api_execution(self, drs_request: dict) -> str:
        """Start DRS execution via REST API."""
        response = requests.post(
            f"{self.drs_api_endpoint}/executions",
            json=drs_request,
            headers=self._get_auth_headers()
        )
        return response.json()["executionId"]
    
    def monitor_execution(self, operation_id: str) -> None:
        """Monitor DRS execution until completion."""
        while True:
            status = self._get_drs_execution_status(operation_id)
            if status["status"] in ["COMPLETED", "FAILED", "CANCELLED"]:
                if status["status"] != "COMPLETED":
                    raise Exception(f"DRS execution failed: {status.get('error')}")
                break
            time.sleep(30)
    
    def generate_results(self, operation_id: str) -> dict:
        """Get comprehensive DRS operation results."""
        drs_results = requests.get(
            f"{self.drs_api_endpoint}/executions/{operation_id}/export",
            headers=self._get_auth_headers()
        ).json()
        
        return {
            "operationId": operation_id,
            "operationType": "drs_orchestration",
            "results": {
                "drsExecution": drs_results,
                "recoveredInstances": drs_results.get("recoveredInstances", []),
                "nextPhaseReady": True
            }
        }
```

### DRS Adapter Configuration

```yaml
drs_adapter_config:
  technology: "drs"
  drs_api_endpoint: "https://api-gateway-url/prod"
  drs_step_function_arn: "arn:aws:states:region:account:stateMachine:drs-orchestrator"
  integration_mode: "api"
  drs_auth_config:
    type: "cognito"
    client_id: "your-cognito-client-id"
    username: "enterprise-platform-service"
    password: "${ssm:/enterprise-dr/drs-service-password}"
```

---

## Database Adapter

The Database Adapter handles RDS and Aurora failover operations.

```python
class DatabaseAdapter(TechnologyAdapter):
    """Database technology adapter for RDS/Aurora failover."""
    
    def __init__(self, config: dict):
        super().__init__("database", config)
        self.rds_client = boto3.client("rds")
    
    def validate_resources(self, resources: list) -> list:
        """Validate RDS/Aurora clusters and instances."""
        validated = []
        for resource in resources:
            if resource.startswith("cluster-"):
                cluster = self.rds_client.describe_db_clusters(
                    DBClusterIdentifier=resource
                )["DBClusters"][0]
                validated.append({
                    "type": "aurora_cluster",
                    "identifier": resource,
                    "engine": cluster["Engine"],
                    "status": cluster["Status"]
                })
            else:
                instance = self.rds_client.describe_db_instances(
                    DBInstanceIdentifier=resource
                )["DBInstances"][0]
                validated.append({
                    "type": "rds_instance",
                    "identifier": resource,
                    "engine": instance["Engine"],
                    "status": instance["DBInstanceStatus"]
                })
        return validated
    
    def start_execution(self, resources: list, config: dict) -> str:
        """Execute database failover operations."""
        execution_id = f"db-exec-{int(time.time())}"
        
        for resource in resources:
            if resource["type"] == "aurora_cluster":
                self.rds_client.failover_db_cluster(
                    DBClusterIdentifier=resource["identifier"],
                    TargetDBInstanceIdentifier=config.get("target_instance")
                )
            elif resource["type"] == "rds_instance":
                self.rds_client.reboot_db_instance(
                    DBInstanceIdentifier=resource["identifier"],
                    ForceFailover=True
                )
        
        return execution_id
    
    def monitor_execution(self, execution_id: str) -> None:
        """Monitor database failover completion."""
        while True:
            all_available = True
            for resource in self.validated_resources:
                if resource["type"] == "aurora_cluster":
                    cluster = self.rds_client.describe_db_clusters(
                        DBClusterIdentifier=resource["identifier"]
                    )["DBClusters"][0]
                    if cluster["Status"] != "available":
                        all_available = False
                        break
            
            if all_available:
                break
            time.sleep(30)
```

---

## Application Adapter

The Application Adapter executes custom application recovery scripts via SSM and Lambda.

```python
class ApplicationAdapter(TechnologyAdapter):
    """Application technology adapter for SSM/Lambda recovery."""
    
    def __init__(self, config: dict):
        super().__init__("application", config)
        self.ssm_client = boto3.client("ssm")
        self.lambda_client = boto3.client("lambda")
    
    def validate_resources(self, resources: list) -> list:
        """Validate application resources."""
        validated = []
        for resource in resources:
            if resource.startswith("i-"):
                validated.append({
                    "type": "ec2_application",
                    "instanceId": resource,
                    "scripts": self.get_application_scripts(resource)
                })
            elif resource.startswith("arn:aws:lambda"):
                validated.append({
                    "type": "lambda_function",
                    "functionArn": resource
                })
        return validated
    
    def start_execution(self, resources: list, config: dict) -> str:
        """Execute application recovery scripts."""
        execution_id = f"app-exec-{int(time.time())}"
        
        for resource in resources:
            if resource["type"] == "ec2_application":
                for script in resource["scripts"]:
                    self.ssm_client.send_command(
                        InstanceIds=[resource["instanceId"]],
                        DocumentName="AWS-RunShellScript",
                        Parameters={"commands": [script["command"]]}
                    )
            elif resource["type"] == "lambda_function":
                self.lambda_client.invoke(
                    FunctionName=resource["functionArn"],
                    InvocationType="Event",
                    Payload=json.dumps({
                        "action": "recovery",
                        "executionId": execution_id
                    })
                )
        
        return execution_id
```

---

## Infrastructure Adapter

The Infrastructure Adapter manages DNS, load balancers, and security groups.

```python
class InfrastructureAdapter(TechnologyAdapter):
    """Infrastructure technology adapter for DNS/ELB/SG."""
    
    def __init__(self, config: dict):
        super().__init__("infrastructure", config)
        self.route53_client = boto3.client("route53")
        self.elbv2_client = boto3.client("elbv2")
        self.ec2_client = boto3.client("ec2")
    
    def start_execution(self, resources: list, config: dict) -> str:
        """Execute infrastructure recovery operations."""
        execution_id = f"infra-exec-{int(time.time())}"
        
        # Update DNS records
        self.update_dns_records(config.get("dns_updates", []))
        
        # Update load balancer targets
        self.update_load_balancer_targets(config.get("lb_updates", []))
        
        # Update security groups
        self.update_security_groups(config.get("sg_updates", []))
        
        return execution_id
    
    def update_dns_records(self, dns_updates: list) -> None:
        """Update Route 53 DNS records for failover."""
        for update in dns_updates:
            self.route53_client.change_resource_record_sets(
                HostedZoneId=update["hosted_zone_id"],
                ChangeBatch={
                    "Changes": [{
                        "Action": "UPSERT",
                        "ResourceRecordSet": {
                            "Name": update["record_name"],
                            "Type": update["record_type"],
                            "TTL": 60,
                            "ResourceRecords": [{"Value": update["new_value"]}]
                        }
                    }]
                }
            )
```

---

## SQL Always On Adapter

The SQL Always On Adapter manages SQL Server Availability Group failover.

```python
class SQLAlwaysOnAdapter(TechnologyAdapter):
    """SQL Server Always On Availability Group DR adapter."""
    
    def validate_resources(self, resources: dict) -> dict:
        """Validate AG configuration and readiness."""
        ag_name = resources.get("availabilityGroup")
        primary_replica = resources.get("primaryReplica")
        secondary_replica = resources.get("secondaryReplica")
        
        health_check = self._check_ag_health(ag_name)
        sync_status = self._check_sync_status(ag_name)
        
        return {
            "valid": health_check and sync_status,
            "agHealth": health_check,
            "syncStatus": sync_status,
            "primaryReplica": primary_replica,
            "secondaryReplica": secondary_replica
        }
    
    def start_execution(self, resources: dict, config: dict) -> str:
        """Execute AG failover via SSM."""
        execution_id = f"sql-ag-exec-{int(time.time())}"
        
        # Execute failover script via SSM
        self.ssm_client.send_command(
            InstanceIds=[resources["secondaryReplica"]],
            DocumentName="AWS-RunPowerShellScript",
            Parameters={
                "commands": [
                    f"Switch-SqlAvailabilityGroup -Path 'SQLSERVER:\\Sql\\{resources['secondaryReplica']}\\DEFAULT\\AvailabilityGroups\\{resources['availabilityGroup']}' -AllowDataLoss"
                ]
            }
        )
        
        return execution_id
```

---

## NetApp ONTAP Adapter

The NetApp ONTAP Adapter manages SnapMirror replication and failover.

```python
class NetAppONTAPAdapter(TechnologyAdapter):
    """NetApp ONTAP SnapMirror DR adapter."""
    
    def __init__(self, config: dict):
        super().__init__("netapp_ontap", config)
        self.fsx_client = boto3.client("fsx")
    
    def start_execution(self, resources: dict, config: dict) -> str:
        """Execute SnapMirror failover."""
        execution_id = f"ontap-exec-{int(time.time())}"
        
        # Break SnapMirror relationship
        self._break_snapmirror(
            resources["sourceVolume"],
            resources["destinationVolume"]
        )
        
        # Make destination writable
        self._make_volume_writable(resources["destinationVolume"])
        
        return execution_id
    
    def _break_snapmirror(self, source: str, destination: str) -> None:
        """Break SnapMirror relationship for failover."""
        # FSx for NetApp ONTAP API call
        pass
```

---

## S3 Cross-Region Adapter

The S3 Cross-Region Adapter manages S3 cross-region replication failover.

```python
class S3CrossRegionAdapter(TechnologyAdapter):
    """S3 Cross-Region Replication DR adapter."""
    
    def __init__(self, config: dict):
        super().__init__("s3_cross_region", config)
        self.s3_client = boto3.client("s3")
    
    def start_execution(self, resources: dict, config: dict) -> str:
        """Execute S3 cross-region failover."""
        execution_id = f"s3-crr-exec-{int(time.time())}"
        
        # Update bucket policy to allow writes to replica
        self._update_bucket_policy(
            resources["replicaBucket"],
            config["writePolicy"]
        )
        
        # Update application configuration to use replica bucket
        self._update_application_config(
            resources["applicationConfig"],
            resources["replicaBucket"]
        )
        
        return execution_id
```

---

## ElastiCache Adapter

The ElastiCache Adapter manages Redis Global Datastore failover operations.

```python
class ElastiCacheAdapter(TechnologyAdapter):
    """ElastiCache Global Datastore DR adapter."""
    
    def __init__(self, config: dict):
        super().__init__("elasticache", config)
        self.elasticache_client = boto3.client("elasticache")
        self.ssm_client = boto3.client("ssm")
    
    def start_execution(self, resources: dict, config: dict) -> str:
        """Execute ElastiCache global datastore failover."""
        execution_id = f"elasticache-exec-{int(time.time())}"
        
        # Disassociate from global replication group
        self.elasticache_client.disassociate_global_replication_group(
            GlobalReplicationGroupId=resources["globalClusterId"],
            ReplicationGroupId=resources["replicationGroupId"],
            ReplicationGroupRegion=config["targetRegion"]
        )
        
        return execution_id
    
    def monitor_execution(self, execution_id: str) -> None:
        """Monitor global cluster disassociation and new cluster creation."""
        while True:
            response = self.elasticache_client.describe_global_replication_groups(
                GlobalReplicationGroupId=self.global_cluster_id
            )
            status = response["GlobalReplicationGroups"][0]["Status"]
            
            if status == "primary-only":
                # Create new global cluster in DR region
                self._create_new_global_cluster()
                break
            time.sleep(30)
    
    def _create_new_global_cluster(self) -> None:
        """Create new global replication group in DR region."""
        self.elasticache_client.create_global_replication_group(
            GlobalReplicationGroupIdSuffix=self.cluster_suffix,
            GlobalReplicationGroupDescription="Global Datastore",
            PrimaryReplicationGroupId=self.replication_group_id
        )
```

---

## MemoryDB Adapter

The MemoryDB Adapter manages MemoryDB for Redis cluster failover using S3 backups.

```python
class MemoryDBAdapter(TechnologyAdapter):
    """MemoryDB for Redis DR adapter."""
    
    def __init__(self, config: dict):
        super().__init__("memorydb", config)
        self.memorydb_client = boto3.client("memorydb")
        self.s3_client = boto3.client("s3")
        self.ssm_client = boto3.client("ssm")
    
    def start_execution(self, resources: dict, config: dict) -> str:
        """Execute MemoryDB cluster restore from S3 backup."""
        execution_id = f"memorydb-exec-{int(time.time())}"
        
        # Get latest backup from S3
        backup_key = self._get_latest_backup(
            resources["backupBucket"],
            resources["backupPrefix"],
            resources["clusterName"]
        )
        
        # Get cluster config from SSM
        cluster_config = self._get_ssm_parameter(resources["configSsmKey"])
        
        # Create cluster from backup
        self.memorydb_client.create_cluster(
            ClusterName=cluster_config["Name"],
            NodeType=cluster_config["NodeType"],
            NumShards=cluster_config["NumberOfShards"],
            SnapshotArns=[f"arn:aws:s3:::{resources['backupBucket']}/{backup_key}"],
            # ... additional config from SSM
        )
        
        return execution_id
    
    def _get_latest_backup(self, bucket: str, prefix: str, cluster_name: str) -> str:
        """Find the latest backup file in S3."""
        response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        filtered = [obj for obj in response["Contents"] 
                   if obj["Key"].startswith(f"{prefix}{cluster_name}-")]
        latest = max(filtered, key=lambda x: x["Key"])
        return latest["Key"]
```

---

## OpenSearch Adapter

The OpenSearch Adapter manages OpenSearch Service cluster scaling for DR.

```python
class OpenSearchAdapter(TechnologyAdapter):
    """OpenSearch Service DR adapter."""
    
    def __init__(self, config: dict):
        super().__init__("opensearch", config)
        self.opensearch_client = boto3.client("opensearch")
    
    def start_execution(self, resources: dict, config: dict) -> str:
        """Execute OpenSearch cluster scaling."""
        execution_id = f"opensearch-exec-{int(time.time())}"
        
        # Scale up cluster for DR
        response = self.opensearch_client.update_domain_config(
            DomainName=resources["domainName"],
            ClusterConfig={
                "InstanceType": config["dataNodeType"],
                "InstanceCount": config["dataNodeCount"],
                "DedicatedMasterEnabled": True,
                "DedicatedMasterType": config["masterNodeType"],
                "DedicatedMasterCount": config["masterNodeCount"],
                "ZoneAwarenessEnabled": True,
                "ZoneAwarenessConfig": {
                    "AvailabilityZoneCount": config["azCount"]
                }
            },
            VPCOptions={
                "SubnetIds": config["subnetIds"]
            },
            EBSOptions={
                "EBSEnabled": True,
                "VolumeType": "gp3",
                "VolumeSize": self._calculate_storage(
                    config["dataNodeCount"], 
                    config["totalStorageSize"]
                )
            }
        )
        
        return response["DomainConfig"]["ChangeProgressDetails"]["ChangeId"]
    
    def monitor_execution(self, change_id: str) -> None:
        """Monitor OpenSearch cluster scaling progress."""
        while True:
            response = self.opensearch_client.describe_domain_change_progress(
                DomainName=self.domain_name,
                ChangeId=change_id
            )
            status = response["ChangeProgressStatus"]["Status"]
            
            if status == "COMPLETED":
                break
            elif status in ["PENDING", "PROCESSING"]:
                time.sleep(60)
            else:
                raise Exception(f"Cluster change failed: {status}")
```

---

## SQLServer RDS Adapter

The SQLServer RDS Adapter manages SQL Server RDS instance failover using automated backups.

```python
class SQLServerAdapter(TechnologyAdapter):
    """SQL Server RDS DR adapter using automated backup replication."""
    
    def __init__(self, config: dict):
        super().__init__("sqlserver", config)
        self.rds_client = boto3.client("rds")
        self.ssm_client = boto3.client("ssm")
    
    def start_execution(self, resources: dict, config: dict) -> str:
        """Execute SQL Server restore from automated backup."""
        execution_id = f"sqlserver-exec-{int(time.time())}"
        
        # Get backup ARN
        backup_response = self.rds_client.describe_db_instance_automated_backups(
            DBInstanceIdentifier=resources["sourceInstanceId"]
        )
        backup_arn = backup_response["DBInstanceAutomatedBackups"][0]["DBInstanceAutomatedBackupsArn"]
        
        # Get cluster config from SSM
        cluster_config = self._get_ssm_parameter(resources["configSsmKey"])
        
        # Restore to point-in-time
        self.rds_client.restore_db_instance_to_point_in_time(
            TargetDBInstanceIdentifier=cluster_config["DBInstanceIdentifier"],
            SourceDBInstanceAutomatedBackupsArn=backup_arn,
            UseLatestRestorableTime=True,
            DBInstanceClass=cluster_config["DBInstanceClass"],
            DBSubnetGroupName=cluster_config["DBSubnetGroup"]["DBSubnetGroupName"],
            VpcSecurityGroupIds=[sg["VpcSecurityGroupId"] 
                                for sg in cluster_config["VpcSecurityGroups"]],
            DeletionProtection=True,
            CopyTagsToSnapshot=True
        )
        
        return execution_id
    
    def cleanup(self, resources: dict) -> str:
        """Store config and delete SQL Server instance."""
        # Store current config in SSM before deletion
        config = self.rds_client.describe_db_instances(
            DBInstanceIdentifier=resources["sourceInstanceId"]
        )["DBInstances"][0]
        
        self._store_ssm_parameter(
            resources["configSsmKey"],
            json.dumps(config, default=str)
        )
        
        # Disable deletion protection and delete
        self.rds_client.modify_db_instance(
            DBInstanceIdentifier=resources["sourceInstanceId"],
            DeletionProtection=False,
            ApplyImmediately=True
        )
        
        self.rds_client.delete_db_instance(
            DBInstanceIdentifier=resources["sourceInstanceId"],
            DeleteAutomatedBackups=False,
            SkipFinalSnapshot=True
        )
    
    def replicate(self, resources: dict) -> None:
        """Start automated backup replication to DR region."""
        cluster_config = self._get_ssm_parameter(resources["configSsmKey"])
        
        self.rds_client.start_db_instance_automated_backups_replication(
            SourceDBInstanceArn=f"arn:aws:rds:{self.source_region}:{self.account_id}:db:{resources['sourceInstanceId']}",
            BackupRetentionPeriod=7,
            KmsKeyId=cluster_config["KmsKeyId"],
            SourceRegion=self.source_region
        )
```

---

## Adapter Registration

Register adapters with the orchestration engine:

```python
# Adapter registry
ADAPTER_REGISTRY = {
    # Core adapters
    "drs": DRSAdapter,
    "database": DatabaseAdapter,
    "application": ApplicationAdapter,
    "infrastructure": InfrastructureAdapter,
    
    # Database adapters
    "aurora_mysql": AuroraMySQLAdapter,
    "sql_always_on": SQLAlwaysOnAdapter,
    "sqlserver": SQLServerAdapter,
    
    # Cache/Search adapters
    "elasticache": ElastiCacheAdapter,
    "memorydb": MemoryDBAdapter,
    "opensearch": OpenSearchAdapter,
    
    # Storage adapters
    "netapp_ontap": NetAppONTAPAdapter,
    "s3_cross_region": S3CrossRegionAdapter,
    
    # Compute adapters
    "ecs": ECSAdapter,
    "autoscaling": AutoScalingAdapter,
    "lambda": LambdaAdapter,
    
    # Network/Events adapters
    "route53": Route53Adapter,
    "eventbridge": EventBridgeAdapter,
    "event_archive": EventArchiveAdapter,
}

def get_adapter(technology_type: str, config: dict) -> TechnologyAdapter:
    """Get adapter instance for technology type."""
    adapter_class = ADAPTER_REGISTRY.get(technology_type)
    if not adapter_class:
        raise ValueError(f"Unknown technology type: {technology_type}")
    return adapter_class(config)
```

### Module Action Mapping

The following table maps module action names (used in manifests) to adapter classes:

| Manifest Action | Adapter Class | Description |
|-----------------|---------------|-------------|
| `AuroraMySQL` | AuroraMySQLAdapter | Aurora MySQL Global Database |
| `DRS` | DRSAdapter | AWS Elastic Disaster Recovery |
| `ECS` | ECSAdapter | ECS Service scaling |
| `AutoScaling` | AutoScalingAdapter | EC2 Auto Scaling groups |
| `R53Record` | Route53Adapter | Route 53 DNS records |
| `EventBridge` | EventBridgeAdapter | EventBridge rules |
| `LambdaFunction` | LambdaAdapter | Lambda function triggers |
| `EventArchive` | EventArchiveAdapter | EventBridge archive replay |
| `ElastiCache` | ElastiCacheAdapter | ElastiCache Global Datastore |
| `MemoryDB` | MemoryDBAdapter | MemoryDB for Redis |
| `OpenSearchService` | OpenSearchAdapter | OpenSearch Service |
| `SQLServer` | SQLServerAdapter | SQL Server RDS |

---

[← Back to Index](./README.md) | [← Previous: API Integration](./03-api-integration.md) | [Next: IAM & Security →](./05-iam-security.md)