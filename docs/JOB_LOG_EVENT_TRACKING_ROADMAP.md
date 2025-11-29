# Job Log Event Tracking - Implementation Roadmap

## Status: PLANNING 📋

**Created**: November 28, 2025, 8:34 PM EST  
**Priority**: ESSENTIAL for production readiness  
**Complexity**: Medium (AWS EventBridge + Lambda modifications)

## Executive Summary

**Current Limitation**: ExecutionPoller only captures final job status (COMPLETED/FAILED) without tracking intermediate events like server launch progress, conversion status, or detailed failure reasons.

**Proposed Solution**: Implement real-time job log event tracking using AWS EventBridge to capture all DRS job state changes and store them in DynamoDB for comprehensive execution monitoring.

**Business Value**:
- **Real-time visibility** into recovery progress (server-by-server)
- **Detailed diagnostics** for failures (which servers failed, why)
- **Audit trail** of all recovery events for compliance
- **Enhanced UI** showing live server launch status
- **Proactive alerting** on individual server failures

## Problem Statement

### Current State: Polling-Only Approach

**How it works now**:
```
ExecutionPoller (EventBridge 60s) → Check job status → Update wave status
```

**What we get**:
- Final job status: COMPLETED or FAILED
- Aggregate success/failure counts
- No intermediate progress
- No server-level details

**What we're missing**:
1. **Server launch progress**: Which servers are launching vs launched
2. **Conversion status**: How far along each server conversion is
3. **Failure details**: Specific error messages per server
4. **Timeline events**: When each state change occurred
5. **Diagnostic context**: Why a job failed (network? permissions? capacity?)

### Impact on Operations

**Debugging failures**:
- ❌ "Job failed" - but which server? Why?
- ❌ Must manually check DRS console for details
- ❌ No correlation between job failure and specific servers
- ❌ Can't identify patterns in failures

**Monitoring progress**:
- ❌ "Job in progress" - but how far along?
- ❌ Can't show users "5 of 6 servers launched"
- ❌ No ETA for completion
- ❌ Users anxious without progress updates

**Operational excellence**:
- ❌ Limited audit trail for compliance
- ❌ No alerting on individual server failures
- ❌ Can't proactively address issues
- ❌ Post-mortem analysis difficult

## Proposed Solution Architecture

### Overview: EventBridge-Driven Event Capture

```
DRS Service
    ↓ (emits events)
EventBridge Rule (DRS job events)
    ↓ (triggers)
JobLogEventHandler Lambda
    ↓ (writes)
DynamoDB (job-log-events table)
    ↓ (read by)
API Handler (GET /executions/{id}/logs)
    ↓ (displays)
Frontend UI (Enhanced execution details)
```

### Components

#### 1. EventBridge Rule

**Rule Definition**:
```json
{
  "source": ["aws.drs"],
  "detail-type": ["DRS Job Log"],
  "detail": {
    "jobID": [{"exists": true}]
  }
}
```

**Event Types Captured**:
- Job started
- Server launch initiated
- Server launching
- Server launched successfully
- Server launch failed
- Conversion started
- Conversion progress updates
- Conversion completed
- Job completed/failed

#### 2. DynamoDB Table: job-log-events

**Primary Key**:
- `JobId` (HASH) - DRS job ID
- `Timestamp` (RANGE) - Event timestamp (ISO 8601)

**Attributes**:
```json
{
  "JobId": "job-abc123",
  "Timestamp": "2025-11-28T20:30:15.000Z",
  "EventType": "SERVER_LAUNCHED",
  "SourceServerId": "s-1234567890abcdef0",
  "EventData": {
    "sourceServerID": "s-1234567890abcdef0",
    "ec2InstanceID": "i-0abc123def456",
    "state": "LAUNCHED",
    "message": "Server launched successfully"
  },
  "EventId": "evt-xyz789",  // Unique event ID for deduplication
  "TTL": 1735430400  // 30 days retention
}
```

**GSI: ExecutionIdIndex**
- `ExecutionId` (HASH) - Links events to our execution tracking
- `Timestamp` (RANGE) - Time-ordered retrieval
- Purpose: Query all events for an execution

#### 3. JobLogEventHandler Lambda

**Purpose**: Process DRS job log events and store in DynamoDB

**Function Flow**:
```python
def lambda_handler(event, context):
    # 1. Extract event details
    job_id = event['detail']['jobID']
    event_type = event['detail']['eventType']
    source_server_id = event['detail'].get('sourceServerID')
    
    # 2. Look up ExecutionId from JobId
    execution_id = find_execution_by_job_id(job_id)
    
    # 3. Store event in DynamoDB
    store_job_log_event(
        job_id=job_id,
        execution_id=execution_id,
        event_type=event_type,
        event_data=event['detail'],
        timestamp=event['time']
    )
    
    # 4. Update execution status if needed
    if event_type in ['JOB_COMPLETED', 'JOB_FAILED']:
        update_execution_status(execution_id, event_type)
```

**Error Handling**:
- Idempotent writes (use EventId for deduplication)
- Dead letter queue for failed events
- CloudWatch metrics for monitoring
- Alerts on processing failures

#### 4. API Handler Enhancements

**New Endpoint**: `GET /executions/{executionId}/logs`

**Response Format**:
```json
{
  "executionId": "exec-abc123",
  "logs": [
    {
      "timestamp": "2025-11-28T20:30:00Z",
      "eventType": "JOB_STARTED",
      "jobId": "job-abc123",
      "message": "Recovery job started for 6 servers"
    },
    {
      "timestamp": "2025-11-28T20:30:15Z",
      "eventType": "SERVER_LAUNCHING",
      "sourceServerId": "s-1234",
      "message": "Launching server prod-web-01"
    },
    {
      "timestamp": "2025-11-28T20:31:30Z",
      "eventType": "SERVER_LAUNCHED",
      "sourceServerId": "s-1234",
      "ec2InstanceId": "i-0abc123",
      "message": "Server prod-web-01 launched successfully"
    }
  ],
  "summary": {
    "totalServers": 6,
    "launched": 4,
    "launching": 2,
    "failed": 0
  }
}
```

**Query Pattern**:
```python
def get_execution_logs(execution_id):
    # Query GSI: ExecutionIdIndex
    response = dynamodb.query(
        IndexName='ExecutionIdIndex',
        KeyConditionExpression='ExecutionId = :exec_id',
        ExpressionAttributeValues={':exec_id': execution_id},
        ScanIndexForward=True  # Chronological order
    )
    return response['Items']
```

#### 5. Frontend UI Enhancements

**Execution Details Modal - Enhanced View**:

```typescript
// New sections in ExecutionDetails.tsx

<ServerProgressTimeline>
  {logs.filter(l => l.eventType.startsWith('SERVER_'))
    .map(log => (
      <TimelineItem>
        <Timestamp>{log.timestamp}</Timestamp>
        <ServerName>{log.serverName}</ServerName>
        <StatusBadge>{log.eventType}</StatusBadge>
        <Message>{log.message}</Message>
      </TimelineItem>
    ))}
</ServerProgressTimeline>

<ServerStatusSummary>
  <ProgressBar>
    Launched: {summary.launched} / {summary.totalServers}
  </ProgressBar>
  <ServerList>
    {servers.map(server => (
      <ServerCard status={server.status}>
        {server.name} - {server.status}
      </ServerCard>
    ))}
  </ServerList>
</ServerStatusSummary>
```

**Real-time Updates**:
```typescript
// Poll for new log events every 3 seconds during active execution
useEffect(() => {
  if (execution.status === 'IN_PROGRESS') {
    const interval = setInterval(() => {
      fetchExecutionLogs(executionId);
    }, 3000);
    return () => clearInterval(interval);
  }
}, [execution.status]);
```

## Implementation Plan

### Phase 1: Infrastructure Setup (2-3 hours)

**Tasks**:
1. Create DynamoDB table: `drs-orchestration-job-log-events-test`
   - Define schema and indexes
   - Configure TTL for automatic cleanup
   - Set capacity mode (on-demand for flexibility)

2. Create EventBridge rule for DRS job events
   - Define event pattern for DRS job logs
   - Test with sample events
   - Configure CloudWatch metrics

3. Create JobLogEventHandler Lambda function
   - Basic event processing
   - DynamoDB write operations
   - Error handling and logging

**CloudFormation Template**:
```yaml
# Add to lambda-stack.yaml or create new job-log-events-stack.yaml

JobLogEventsTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: !Sub 'drs-orchestration-job-log-events-${Environment}'
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: JobId
        AttributeType: S
      - AttributeName: Timestamp
        AttributeType: S
      - AttributeName: ExecutionId
        AttributeType: S
    KeySchema:
      - AttributeName: JobId
        KeyType: HASH
      - AttributeName: Timestamp
        KeyType: RANGE
    GlobalSecondaryIndexes:
      - IndexName: ExecutionIdIndex
        KeySchema:
          - AttributeName: ExecutionId
            KeyType: HASH
          - AttributeName: Timestamp
            KeyType: RANGE
        Projection:
          ProjectionType: ALL
    TimeToLiveSpecification:
      AttributeName: TTL
      Enabled: true

DRSJobEventsRule:
  Type: AWS::Events::Rule
  Properties:
    Name: !Sub 'drs-job-events-${Environment}'
    EventPattern:
      source:
        - aws.drs
      detail-type:
        - DRS Job Log
    Targets:
      - Arn: !GetAtt JobLogEventHandlerFunction.Arn
        Id: JobLogEventHandler

JobLogEventHandlerFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: !Sub 'drs-orchestration-job-log-handler-${Environment}'
    Runtime: python3.11
    Handler: job_log_handler.lambda_handler
    Role: !GetAtt JobLogEventHandlerRole.Arn
    Environment:
      Variables:
        JOB_LOG_EVENTS_TABLE: !Ref JobLogEventsTable
        EXECUTION_HISTORY_TABLE: !Ref ExecutionHistoryTable
```

### Phase 2: Lambda Function Development (2-3 hours)

**File**: `lambda/job_log_handler.py`

```python
import boto3
import json
import os
from datetime import datetime, timedelta
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
job_log_table = dynamodb.Table(os.environ['JOB_LOG_EVENTS_TABLE'])
execution_table = dynamodb.Table(os.environ['EXECUTION_HISTORY_TABLE'])

def lambda_handler(event, context):
    """Process DRS job log events and store in DynamoDB."""
    
    try:
        # Extract event details
        detail = event['detail']
        job_id = detail['jobID']
        event_time = event['time']
        event_type = detail.get('eventType', 'UNKNOWN')
        
        # Look up execution ID from job ID
        execution_id = find_execution_by_job_id(job_id)
        
        if not execution_id:
            print(f"No execution found for job {job_id}")
            return {'statusCode': 200, 'body': 'No execution found'}
        
        # Create event record
        event_record = {
            'JobId': job_id,
            'Timestamp': event_time,
            'ExecutionId': execution_id,
            'EventType': event_type,
            'EventData': json.loads(json.dumps(detail), parse_float=Decimal),
            'EventId': event.get('id', f"{job_id}-{event_time}"),
            'TTL': int((datetime.utcnow() + timedelta(days=30)).timestamp())
        }
        
        # Store in DynamoDB
        job_log_table.put_item(
            Item=event_record,
            ConditionExpression='attribute_not_exists(EventId)'  # Deduplication
        )
        
        print(f"Stored event: {event_type} for job {job_id}")
        
        # Update execution status if job completed/failed
        if event_type in ['JOB_COMPLETED', 'JOB_FAILED']:
            update_execution_from_event(execution_id, detail)
        
        return {'statusCode': 200, 'body': 'Event processed'}
        
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        # Duplicate event - already processed
        print(f"Duplicate event {event.get('id')} - skipping")
        return {'statusCode': 200, 'body': 'Duplicate event'}
    
    except Exception as e:
        print(f"Error processing event: {str(e)}")
        raise

def find_execution_by_job_id(job_id):
    """Find execution ID from job ID by scanning execution history."""
    # Query execution history table for job ID
    # This requires adding JobId to execution records
    response = execution_table.scan(
        FilterExpression='contains(#data, :job_id)',
        ExpressionAttributeNames={'#data': 'WaveData'},
        ExpressionAttributeValues={':job_id': job_id}
    )
    
    if response['Items']:
        return response['Items'][0]['ExecutionId']
    return None

def update_execution_from_event(execution_id, event_detail):
    """Update execution status based on job event."""
    # Extract final status and update execution
    final_status = 'COMPLETED' if event_detail['eventType'] == 'JOB_COMPLETED' else 'FAILED'
    
    execution_table.update_item(
        Key={'ExecutionId': execution_id},
        UpdateExpression='SET #status = :status, EndTime = :end_time',
        ExpressionAttributeNames={'#status': 'Status'},
        ExpressionAttributeValues={
            ':status': final_status,
            ':end_time': datetime.utcnow().isoformat()
        }
    )
```

### Phase 3: API Handler Integration (1-2 hours)

**Add to `lambda/index.py`**:

```python
@app.route('/executions/<execution_id>/logs', methods=['GET'])
def get_execution_logs(execution_id):
    """Get job log events for an execution."""
    
    try:
        # Query job log events by execution ID
        response = dynamodb.query(
            TableName=os.environ['JOB_LOG_EVENTS_TABLE'],
            IndexName='ExecutionIdIndex',
            KeyConditionExpression='ExecutionId = :exec_id',
            ExpressionAttributeValues={':exec_id': {'S': execution_id}},
            ScanIndexForward=True  # Chronological order
        )
        
        # Transform events for frontend
        logs = []
        summary = {
            'totalServers': 0,
            'launched': 0,
            'launching': 0,
            'failed': 0
        }
        
        for item in response['Items']:
            event = {
                'timestamp': item['Timestamp']['S'],
                'eventType': item['EventType']['S'],
                'jobId': item['JobId']['S'],
                'message': item['EventData']['M'].get('message', {}).get('S', ''),
                'sourceServerId': item['EventData']['M'].get('sourceServerID', {}).get('S')
            }
            logs.append(event)
            
            # Update summary counts
            if event['eventType'] == 'SERVER_LAUNCHED':
                summary['launched'] += 1
            elif event['eventType'] == 'SERVER_LAUNCHING':
                summary['launching'] += 1
            elif event['eventType'] == 'SERVER_LAUNCH_FAILED':
                summary['failed'] += 1
        
        return jsonify({
            'executionId': execution_id,
            'logs': logs,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Phase 4: Frontend UI Development (2-3 hours)

**Create**: `frontend/src/components/ExecutionLogViewer.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import {
  Box,
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  Typography,
  Paper,
  LinearProgress
} from '@mui/material';
import { CheckCircle, Error, HourglassEmpty } from '@mui/icons-material';
import { DateTimeDisplay } from './DateTimeDisplay';
import apiClient from '../services/api';

interface ExecutionLog {
  timestamp: string;
  eventType: string;
  message: string;
  sourceServerId?: string;
}

interface LogSummary {
  totalServers: number;
  launched: number;
  launching: number;
  failed: number;
}

export const ExecutionLogViewer: React.FC<{ executionId: string }> = ({
  executionId
}) => {
  const [logs, setLogs] = useState<ExecutionLog[]>([]);
  const [summary, setSummary] = useState<LogSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await apiClient.getExecutionLogs(executionId);
        setLogs(response.logs);
        setSummary(response.summary);
      } catch (error) {
        console.error('Failed to fetch logs:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchLogs();
    
    // Poll every 3 seconds for updates
    const interval = setInterval(fetchLogs, 3000);
    return () => clearInterval(interval);
  }, [executionId]);

  const getEventIcon = (eventType: string) => {
    if (eventType.includes('LAUNCHED')) return <CheckCircle color="success" />;
    if (eventType.includes('FAILED')) return <Error color="error" />;
    return <HourglassEmpty color="warning" />;
  };

  if (loading) return <Typography>Loading logs...</Typography>;

  return (
    <Box>
      {summary && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Server Launch Progress
          </Typography>
          <LinearProgress 
            variant="determinate" 
            value={(summary.launched / summary.totalServers) * 100}
            sx={{ height: 10, borderRadius: 1, mb: 1 }}
          />
          <Typography variant="body2">
            {summary.launched} of {summary.totalServers} servers launched
            {summary.failed > 0 && ` (${summary.failed} failed)`}
          </Typography>
        </Paper>
      )}

      <Timeline>
        {logs.map((log, index) => (
          <TimelineItem key={index}>
            <TimelineSeparator>
              <TimelineDot>
                {getEventIcon(log.eventType)}
              </TimelineDot>
              {index < logs.length - 1 && <TimelineConnector />}
            </TimelineSeparator>
            <TimelineContent>
              <Typography variant="caption" color="text.secondary">
                <DateTimeDisplay value={log.timestamp} format="full" />
              </Typography>
              <Typography variant="body2">
                {log.message}
              </Typography>
              {log.sourceServerId && (
                <Typography variant="caption" color="text.secondary">
                  Server: {log.sourceServerId}
                </Typography>
              )}
            </TimelineContent>
          </TimelineItem>
        ))}
      </Timeline>
    </Box>
  );
};
```

**Integrate into ExecutionDetails**:
```typescript
// Add to ExecutionDetails.tsx
import { ExecutionLogViewer } from './ExecutionLogViewer';

// Add tab for logs
<Tab label="Job Logs" />

// Add tab panel
<TabPanel value={tabValue} index={2}>
  <ExecutionLogViewer executionId={executionId} />
</TabPanel>
```

### Phase 5: Testing & Validation (2 hours)

**Test Scenarios**:

1. **Happy Path - All Servers Launch Successfully**
   - Start recovery drill with 3 servers
   - Verify all events captured:
     - JOB_STARTED
     - SERVER_LAUNCHING (x3)
     - SERVER_LAUNCHED (x3)
     - JOB_COMPLETED
   - Verify UI shows progress: 0/3 → 1/3 → 2/3 → 3/3
   - Verify timeline displays all events

2. **Failure Scenario - One Server Fails**
   - Start recovery with 3 servers
   - Simulate failure on one server
   - Verify events:
     - SERVER_LAUNCH_FAILED captured
     - Error details included
     - Job still completes for other servers
   - Verify UI highlights failed server

3. **Real-time Updates**
   - Start execution
   - Open execution details
   - Verify logs appear in real-time (3s refresh)
   - Verify progress bar updates live

4. **Historical Logs**
   - Complete execution
   - Navigate away and back
   - Verify all logs still available
   - Verify no polling on completed execution

5. **Error Handling**
   - Duplicate events (EventBridge retries)
   - Missing execution ID
   - DynamoDB throttling
   - API errors

### Phase 6: Deployment (1 hour)

**Deployment Order**:
1. Deploy DynamoDB table (CloudFormation)
2. Deploy EventBridge rule
3. Deploy JobLogEventHandler Lambda
4. Deploy updated API Handler Lambda
5. Deploy updated Frontend
6. Verify EventBridge rule is active
7. Test with sample DRS event
8. Monitor CloudWatch logs

**Monitoring Setup**:
```yaml
# CloudWatch Alarms
JobLogEventHandlerErrors:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub '${Environment}-job-log-handler-errors'
    MetricName: Errors
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 5
    ComparisonOperator: GreaterThanThreshold

EventProcessingLag:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub '${Environment}-event-processing-lag'
    MetricName: Duration
    Namespace: AWS/Lambda
    Statistic: Average
    Period: 60
    EvaluationPeriods: 2
    Threshold: 5000  # 5 seconds
    ComparisonOperator: GreaterThanThreshold
```

## Benefits & ROI

### Operational Benefits

**Debugging Time Reduction**: 80%
- Before: 30 minutes to correlate job failure with server/error
- After: 2 minutes to see exact failure in logs

**User Satisfaction**: +50%
- Real-time progress updates reduce anxiety
- Clear visibility into what's happening
- Professional enterprise-grade monitoring

**Proactive Issue Detection**
- Alert on first server failure (don't wait for job to complete)
- Identify patterns in failures (specific servers, regions, etc.)
- Capacity planning (track conversion times)

### Technical Benefits

**Complete Audit Trail**
- Compliance: Full history of all recovery events
- Forensics: Exactly what happened when
- Reporting: Aggregate metrics on recovery operations

**Enhanced Diagnostics**
- Server-level failure details
- Network/permissions issues identified quickly
- DRS API behavior visible

**Production Readiness**
- Enterprise-grade monitoring
- Operational excellence
- Customer confidence

## Cost Analysis

### Infrastructure Costs

**DynamoDB**:
- On-demand pricing
- ~100 events per execution
- ~$0.25 per 1M write requests
- Estimated: $5/month for 200 executions

**Lambda**:
- JobLogEventHandler: 128MB, <1s execution
- ~100 invocations per execution
- Estimated: $2/month for 200 executions

**EventBridge**:
- $1 per million events
- Negligible cost

**Total Monthly Cost**: ~$7 (minimal)

### Time Investment

**Development**: 10-12 hours
- Infrastructure: 2-3 hours
- Lambda: 2-3 hours
- API: 1-2 hours
- Frontend: 2-3 hours
- Testing: 2 hours
- Deployment: 1 hour

**Maintenance**: <1 hour/month
- Monitor CloudWatch metrics
- Investigate any processing errors
- Adjust TTL if needed

**ROI**: 
- Debugging time saved: 5 hours/week × 4 weeks = 20 hours/month
- Implementation cost: 12 hours one-time
- **Payback period**: < 1 month

## Risks & Mitigations

### Technical Risks

**Risk: EventBridge event delivery failure**
- Mitigation: Dead letter queue for failed events
- Mitigation: CloudWatch alarms on processing errors
- Mitigation: Replay capability from DRS CloudTrail logs

**Risk: DynamoDB throttling**
- Mitigation: On-demand capacity mode (auto-scales)
- Mitigation: Exponential backoff in Lambda
- Mitigation: Monitor ConsumedReadCapacityUnits/ConsumedWriteCapacityUnits

**Risk: Event duplication**
- Mitigation: Idempotent writes using EventId
- Mitigation: ConditionalCheckFailed handling
- Mitigation: Deduplication in frontend display

**Risk: ExecutionId lookup failures**
- Mitigation: Fallback to job-level tracking
- Mitigation: Graceful degradation (logs still captured)
- Mitigation: Background job to link orphaned events

### Operational Risks

**Risk: High volume of events**
- Mitigation: TTL for automatic cleanup (30 days)
- Mitigation: Pagination in API responses
- Mitigation: Frontend virtualized list for large logs

**Risk: EventBridge rule misconfiguration**
- Mitigation: Comprehensive testing with sample events
- Mitigation: CloudWatch metrics on rule invocations
- Mitigation: Documented rollback procedure

## Alternatives Considered

### Alternative 1: Polling DRS Logs API

**Approach**: Poll DRS DescribeJobLogItems API periodically

**Pros**:
- No EventBridge dependency
- Simpler infrastructure

**Cons**:
- Delayed updates (polling lag)
- Higher DRS API costs
- Rate limiting concerns
- More complex state management

**Decision**: Rejected - EventBridge provides real-time updates

### Alternative 2: CloudWatch Logs Insights

**Approach**: Parse DRS CloudWatch logs

**Pros**:
- No custom storage needed
- Integrated with AWS logging

**Cons**:
- Query performance issues
- Complex log parsing
- No structured data
- Difficult to correlate with executions

**Decision**: Rejected - DynamoDB provides better structure

### Alternative 3: Minimal Approach (Status Only)

**Approach**: Keep current polling-only system

**Pros**:
- No additional development
- Simplest solution

**Cons**:
- Poor user experience
- Difficult debugging
- Not production-ready

**Decision**: Rejected - Benefits far outweigh costs

## Success Criteria

### Functional Requirements

✅ Capture all DRS job log events  
✅ Store events in DynamoDB with 30-day retention  
✅ Link events to executions via ExecutionId  
✅ Provide API endpoint for log retrieval  
✅ Display real-time logs in UI  
✅ Show server-by-server progress  
✅ Highlight failures with details  
✅ Handle duplicate events gracefully  
✅ Scale to 100+ concurrent executions

### Performance Requirements

✅ Event processing latency < 5 seconds  
✅ API response time < 500ms for 100 events  
✅ Frontend refresh interval 3 seconds  
✅ DynamoDB query time < 100ms  
✅ Zero data loss on events  

### Operational Requirements

✅ CloudWatch alarms configured  
✅ Error rate < 0.1%  
✅ Dead letter queue monitored  
✅ Monthly cost < $10  
✅ Zero manual intervention needed  

## Next Steps

### Immediate (This Week)

1. Review this roadmap with stakeholders
2. Get approval for implementation
3. Schedule development sprint
4. Create CloudFormation templates
5. Set up development environment

### Short Term (Next Sprint)

1. Implement Phase 1 (Infrastructure)
2. Develop Phase 2 (Lambda)
3. Test with sample events
4. Validate event capture

### Medium Term (Following Sprint)

1. Implement Phase 3 (API integration)
2. Develop Phase 4 (Frontend UI)
3. Comprehensive testing
4. Deploy to test environment

### Long Term (Production)

1. Production deployment
2. Monitor for 2 weeks
3. Gather user feedback
4. Iterate on UI/UX improvements

## Appendix

### DRS Event Types Reference

**Job-Level Events**:
- `JOB_STARTED` - Recovery job initiated
- `JOB_COMPLETED` - Job finished successfully
- `JOB_FAILED` - Job failed
- `JOB_TERMINATED` - Job manually stopped

**Server-Level Events**:
- `SERVER_LAUNCHING` - Server launch initiated
- `SERVER_LAUNCHED` - Server successfully launched
- `SERVER_LAUNCH_FAILED` - Server launch failed
- `CONVERSION_STARTED` - Server conversion began
- `CONVERSION_IN_PROGRESS` - Conversion progress update
- `CONVERSION_COMPLETED` - Conversion finished

### Sample Event Payloads

**JOB_STARTED Event**:
```json
{
  "version": "0",
  "id": "abc-123",
  "detail-type": "DRS Job Log",
  "source": "aws.drs",
  "time": "2025-11-28T20:30:00Z",
  "detail": {
    "jobID": "job-abc123",
    "eventType": "JOB_STARTED",
    "isDrill": true,
    "sourceServerIDs": [
      "s-1234567890abcdef0",
      "s-2345678901abcdef1"
