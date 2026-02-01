# AWS Elastic Disaster Recovery (DRS) Service Quotas - Complete Reference

**Source**: [AWS General Reference - DRS Endpoints and Quotas](https://docs.aws.amazon.com/general/latest/gr/drs.html)  
**Last Updated**: January 31, 2026

## Critical Understanding: Replication vs Recovery Capacity

### Key Distinction
- **Replicating servers**: Servers actively replicating data TO an AWS account (300 max per account)
- **Source servers**: Total servers that can be RECOVERED FROM an account (4,000 max per account)

### The Staging Account Pattern

This is how you exceed 300 replicating servers:

```
┌─────────────────────────────────────────────────────────────┐
│ Scenario: 500 servers need DR protection                    │
└─────────────────────────────────────────────────────────────┘

Step 1: Split replication across accounts
┌──────────────────────┐         ┌──────────────────────┐
│  Staging Account A   │         │  Staging Account B   │
│  250 servers         │         │  250 servers         │
│  replicating         │         │  replicating         │
└──────────────────────┘         └──────────────────────┘
         │                                  │
         │ Extended as source servers       │
         └──────────────┬───────────────────┘
                        ▼
              ┌──────────────────────┐
              │   Target Account     │
              │   500 source servers │
              │   (250 + 250)        │
              │   All can recover    │
              │   into this account  │
              └──────────────────────┘

Result: All 500 servers visible in Target Account console
        All 500 can recover into Target Account
        No replication limit exceeded (250 < 300 per account)
```

## Complete Service Quotas

| Quota Name | Limit | Adjustable | Description |
|------------|-------|------------|-------------|
| **Max Total replicating source servers Per AWS Account** | 300 | ❌ No | Maximum servers actively replicating TO this account |
| **Max Total source servers Per AWS Account** | 4,000 | ✅ Yes | Maximum servers that can be recovered FROM this account (includes extended source servers) |
| **Concurrent jobs in progress** | 20 | ❌ No | Maximum recovery/drill jobs running simultaneously |
| **Max source servers in a single Job** | 100 | ❌ No | Maximum servers in one recovery/drill operation |
| **Max source servers in all Jobs** | 500 | ❌ No | Maximum servers across all concurrent jobs |
| **Max concurrent Jobs per source server** | 1 | ❌ No | A server can only be in one job at a time |
| **Max number of launch actions per resource** | 200 | ❌ No | Maximum pre/post launch actions per server |
| **Max number of launch configuration templates per AWS account** | 1 | ❌ No | Single launch template per account |
| **Max number of source networks per AWS account** | 100 | ✅ Yes | Maximum source networks for network replication |

## Capacity Planning Examples

### Example 1: Single Account (Up to 300 servers)
```
Replicating: 300 servers
Source servers: 300 servers
Recovery capacity: 300 servers
```

### Example 2: Two Staging Accounts (Up to 600 servers)
```
Staging Account A: 300 replicating → extended to Target
Staging Account B: 300 replicating → extended to Target
Target Account: 600 source servers (all can recover)
```

### Example 3: Maximum Scale (Up to 4,000 servers)
```
Staging Account 1: 300 replicating → extended to Target
Staging Account 2: 300 replicating → extended to Target
Staging Account 3: 300 replicating → extended to Target
...
Staging Account 13: 300 replicating → extended to Target
Staging Account 14: 100 replicating → extended to Target

Target Account: 4,000 source servers (maximum)
```

### Example 4: Recovery Job Constraints
```
Scenario: 500 source servers in Target Account

Constraint 1: Max 20 concurrent jobs
Constraint 2: Max 100 servers per job
Constraint 3: Max 500 servers across all jobs

Recovery Strategy:
- Wave 1: 5 jobs × 100 servers = 500 servers (uses all 500 quota)
- Wave 2: Must wait for Wave 1 to complete
- OR: 5 jobs × 80 servers = 400 servers (leaves buffer)
```

## Important Notes

### Replication Limits (300 per account)
- **Cannot be increased** - hard limit
- Applies to servers actively replicating TO the account
- Does NOT apply to extended source servers
- Workaround: Use multiple staging accounts

### Source Server Limits (4,000 per account)
- **Can be increased** via AWS Support
- Applies to total servers that can recover FROM the account
- Includes both:
  - Servers replicating directly to this account
  - Extended source servers from staging accounts

### Job Execution Limits
- **20 concurrent jobs**: Cannot run more than 20 recovery/drill operations simultaneously
- **100 servers per job**: Each job can include up to 100 servers
- **500 servers across all jobs**: Total servers in all concurrent jobs cannot exceed 500
- **1 job per server**: A server cannot be in multiple jobs simultaneously

### Launch Configuration
- **1 template per account**: Single launch configuration template
- **200 launch actions per resource**: Pre/post launch scripts/actions per server

## Architectural Implications

### For DR Orchestration Platform

1. **Staging Account Management**
   - Track replication count per staging account (max 300)
   - Automatically distribute servers across staging accounts
   - Monitor extended source server relationships

2. **Recovery Job Orchestration**
   - Respect 20 concurrent job limit
   - Batch servers into groups of ≤100 per job
   - Ensure total servers across jobs ≤500
   - Implement wave-based recovery for large-scale DR

3. **Capacity Monitoring**
   - Alert when approaching 300 replicating servers per account
   - Track total source servers against 4,000 limit
   - Monitor job execution capacity (20 concurrent, 500 total)

4. **Scaling Strategy**
   - Add staging accounts when approaching 300 replicating servers
   - Request quota increase for source servers if approaching 4,000
   - Implement job queuing for large-scale recoveries

## API Considerations

### Key DRS API Calls
```python
# Check replication capacity
response = drs_client.describe_source_servers()
replicating_count = len([s for s in response['items'] 
                        if s['replicationStatus'] == 'REPLICATING'])

# Check job capacity
response = drs_client.describe_jobs(
    filters={'jobIDs': [], 'fromDate': datetime.now()}
)
active_jobs = len([j for j in response['items'] 
                  if j['status'] in ['PENDING', 'STARTED']])

# Check servers in jobs
total_servers_in_jobs = sum(len(j['participatingServers']) 
                           for j in response['items'])
```

## Related Documentation

- [DRS Service Limits and Capabilities](DRS_SERVICE_LIMITS_AND_CAPABILITIES.md)
- [DRS Cross-Account Reference](DRS_CROSS_ACCOUNT_REFERENCE.md)
- [Extended Source Server Capacity Design](../guides/EXTENDED_SOURCE_SERVER_CAPACITY_DESIGN.md)

## References

- [AWS DRS Service Quotas](https://docs.aws.amazon.com/general/latest/gr/drs.html)
- [AWS Service Quotas Console](https://console.aws.amazon.com/servicequotas/)
- [AWS DRS User Guide](https://docs.aws.amazon.com/drs/latest/userguide/)
