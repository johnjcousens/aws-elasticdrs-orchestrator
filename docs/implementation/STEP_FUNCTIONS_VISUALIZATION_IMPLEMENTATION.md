# Step Functions Visualization Implementation Plan

**Version:** 1.0  
**Date:** January 2025  
**Status:** Ready for Implementation  
**Estimated Effort:** 2-3 weeks

---

## Executive Summary

### Problem Statement

Currently, when a Recovery Plan execution is running, users can see wave-level progress but have no visibility into the underlying Step Functions state machine orchestration. This makes it difficult to:
- Understand which Step Functions state is currently executing
- Diagnose stuck or failed executions at the state machine level
- Visualize the orchestration flow and decision points
- Debug issues with pause/resume or wave transitions

### Solution Overview

Integrate Step Functions execution visualization directly into the Execution Details page, providing:
- **Real-time State Tracking**: Display current Step Functions state with visual indicators
- **State History Timeline**: Show progression through states with timestamps
- **Interactive State Diagram**: Visual representation of the state machine flow
- **State Details Panel**: Input/output data for each state transition
- **CloudWatch Logs Integration**: Deep-link to logs for each state

### Business Value

- **Faster Troubleshooting**: Reduce time to diagnose execution issues by 80%
- **Operational Transparency**: Complete visibility into orchestration engine
- **Better User Experience**: Users understand what's happening "under the hood"
- **Debugging Capability**: Developers can trace execution flow for issues

---

## Current Architecture Analysis

### Step Functions State Machine

The DRS Orchestration state machine has **9 states**:

```
InitiateWavePlan (Task)
  ↓
DetermineWavePlanState (Choice)
  ↓ [all_waves_completed=false]
DetermineWaveState (Choice)
  ↓ [wave_completed=false]
WaitForWaveUpdate (Wait)
  ↓
UpdateWaveStatus (Task)
  ↓ [loop back to DetermineWaveState]
  
  ↓ [status=paused]
WaitForResume (Task - callback)
  ↓
ResumeWavePlan (Task)
  ↓ [back to DetermineWaveState]
  
  ↓ [all_waves_completed=true]
PlanCompleted (Succeed)

  ↓ [status=failed]
PlanFailed (Fail)

  ↓ [status=timeout]
PlanTimeout (Fail)
```

### State Transitions

| State | Type | Next States | Typical Duration |
|-------|------|-------------|------------------|
| InitiateWavePlan | Task | DetermineWavePlanState | 1-2s |
| DetermineWavePlanState | Choice | DetermineWaveState, WaitForResume, PlanCompleted, PlanFailed, PlanTimeout | <1s |
| DetermineWaveState | Choice | WaitForWaveUpdate, DetermineWavePlanState, PlanFailed, PlanTimeout | <1s |
| WaitForWaveUpdate | Wait | UpdateWaveStatus | 30s (configurable) |
| UpdateWaveStatus | Task | DetermineWaveState | 2-5s |
| WaitForResume | Task (callback) | ResumeWavePlan | Minutes to hours |
| ResumeWavePlan | Task | DetermineWaveState | 1-2s |
| PlanCompleted | Succeed | - | Terminal |
| PlanFailed | Fail | - | Terminal |
| PlanTimeout | Fail | - | Terminal |

### Current Data Flow

1. **Frontend** polls `/executions/{id}` every 3 seconds
2. **API** returns execution data from DynamoDB
3. **DynamoDB** stores wave-level status (not state machine states)
4. **Step Functions** execution history is NOT currently exposed to frontend

---

## Implementation Design

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         ExecutionDetailsPage.tsx                      │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │  StepFunctionsVisualization Component          │  │   │
│  │  │  - State Timeline                               │  │   │
│  │  │  - Current State Indicator                      │  │   │
│  │  │  - State Diagram (optional)                     │  │   │
│  │  │  - State Details Panel                          │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │ GET /executions/{id}/step-functions
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    API Gateway + Lambda                      │
│                                                               │
│  get_execution_step_functions_history()                      │
│  - Fetch execution ARN from DynamoDB                         │
│  - Call StepFunctions.get_execution_history()                │
│  - Transform events to frontend format                       │
│  - Return state timeline with current state                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    AWS Step Functions                        │
│                                                               │
│  - Execution History (events)                                │
│  - Current execution status                                  │
│  - State input/output data                                   │
└─────────────────────────────────────────────────────────────┘
```

### Data Model

#### Step Functions Event Types

```typescript
interface StepFunctionsEvent {
  timestamp: number;
  type: string;  // ExecutionStarted, TaskStateEntered, TaskStateExited, etc.
  id: number;
  previousEventId?: number;
  stateEnteredEventDetails?: {
    name: string;
    input?: string;
  };
  stateExitedEventDetails?: {
    name: string;
    output?: string;
  };
  executionFailedEventDetails?: {
    error?: string;
    cause?: string;
  };
}

interface StepFunctionsState {
  name: string;
  type: 'Task' | 'Choice' | 'Wait' | 'Succeed' | 'Fail';
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  enteredAt?: number;
  exitedAt?: number;
  duration?: number;
  input?: any;
  output?: any;
  error?: string;
}

interface StepFunctionsExecution {
  executionArn: string;
  stateMachineArn: string;
  status: 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'TIMED_OUT' | 'ABORTED';
  startDate: number;
  stopDate?: number;
  currentState?: string;
  states: StepFunctionsState[];
}
```

---

## Implementation Phases

### Phase 1: Backend API (Week 1)

#### 1.1 Add Step Functions History Endpoint

Add to `lambda/index.py`:

```python
def get_execution_step_functions_history(execution_id: str) -> Dict:
    """
    Get Step Functions execution history for an execution
    
    Returns:
    - executionArn: Step Functions execution ARN
    - status: Current execution status
    - currentState: Name of current state
    - states: List of states with entry/exit times
    - events: Raw Step Functions events (optional)
    """
    try:
        # Get execution from DynamoDB
        execution_history_table = dynamodb.Table(EXECUTION_HISTORY_TABLE)
        response = execution_history_table.scan(
            FilterExpression=Attr('ExecutionId').eq(execution_id)
        )
        
        if not response.get('Items'):
            return response(404, {'error': 'Execution not found'})
        
        execution = response['Items'][0]
        
        # Get Step Functions execution ARN
        # Format: arn:aws:states:region:account:execution:state-machine-name:execution-id
        state_machine_arn = os.environ.get('STATE_MACHINE_ARN')
        if not state_machine_arn:
            return response(500, {'error': 'STATE_MACHINE_ARN not configured'})
        
        # Construct execution ARN
        execution_arn = f"{state_machine_arn.replace(':stateMachine:', ':execution:')}:{execution_id}"
        
        # Get execution history from Step Functions
        sfn_client = boto3.client('stepfunctions')
        
        # Get execution status
        try:
            exec_response = sfn_client.describe_execution(executionArn=execution_arn)
            execution_status = exec_response['status']
            start_date = exec_response['startDate'].timestamp()
            stop_date = exec_response.get('stopDate')
            stop_date_ts = stop_date.timestamp() if stop_date else None
        except sfn_client.exceptions.ExecutionDoesNotExist:
            return response(404, {'error': 'Step Functions execution not found'})
        
        # Get execution history events
        history_response = sfn_client.get_execution_history(
            executionArn=execution_arn,
            maxResults=1000,
            reverseOrder=False
        )
        
        events = history_response.get('events', [])
        
        # Transform events to state timeline
        states = transform_events_to_states(events)
        
        # Determine current state
        current_state = None
        if execution_status == 'RUNNING':
            # Find last entered state that hasn't exited
            for state in reversed(states):
                if state['status'] == 'in_progress':
                    current_state = state['name']
                    break
        
        return response(200, {
            'executionArn': execution_arn,
            'stateMachineArn': state_machine_arn,
            'status': execution_status,
            'startDate': start_date,
            'stopDate': stop_date_ts,
            'currentState': current_state,
            'states': states,
            'totalEvents': len(events)
        })
        
    except Exception as e:
        print(f"Error getting Step Functions history: {e}")
        import traceback
        traceback.print_exc()
        return response(500, {'error': str(e)})


def transform_events_to_states(events: List[Dict]) -> List[Dict]:
    """
    Transform Step Functions events into state timeline
    
    Groups StateEntered/StateExited events into state objects
    """
    states = []
    state_map = {}  # name -> state object
    
    for event in events:
        event_type = event['type']
        timestamp = event['timestamp'].timestamp()
        
        if event_type == 'TaskStateEntered' or event_type == 'ChoiceStateEntered' or event_type == 'WaitStateEntered':
            details = event.get('stateEnteredEventDetails', {})
            state_name = details.get('name')
            
            if state_name:
                state_obj = {
                    'name': state_name,
                    'type': event_type.replace('StateEntered', ''),
                    'status': 'in_progress',
                    'enteredAt': timestamp,
                    'input': details.get('input')
                }
                state_map[state_name] = state_obj
                states.append(state_obj)
        
        elif event_type == 'TaskStateExited' or event_type == 'ChoiceStateExited' or event_type == 'WaitStateExited':
            details = event.get('stateExitedEventDetails', {})
            state_name = details.get('name')
            
            if state_name and state_name in state_map:
                state_obj = state_map[state_name]
                state_obj['status'] = 'completed'
                state_obj['exitedAt'] = timestamp
                state_obj['duration'] = timestamp - state_obj['enteredAt']
                state_obj['output'] = details.get('output')
        
        elif event_type == 'TaskFailed':
            details = event.get('taskFailedEventDetails', {})
            # Find the state that failed
            for state in reversed(states):
                if state['status'] == 'in_progress':
                    state['status'] = 'failed'
                    state['exitedAt'] = timestamp
                    state['duration'] = timestamp - state['enteredAt']
                    state['error'] = details.get('error')
                    state['cause'] = details.get('cause')
                    break
        
        elif event_type == 'ExecutionSucceeded':
            # Mark last state as completed if still in progress
            for state in reversed(states):
                if state['status'] == 'in_progress':
                    state['status'] = 'completed'
                    state['exitedAt'] = timestamp
                    state['duration'] = timestamp - state['enteredAt']
                    break
        
        elif event_type == 'ExecutionFailed':
            details = event.get('executionFailedEventDetails', {})
            # Mark last state as failed
            for state in reversed(states):
                if state['status'] == 'in_progress':
                    state['status'] = 'failed'
                    state['exitedAt'] = timestamp
                    state['duration'] = timestamp - state['enteredAt']
                    state['error'] = details.get('error')
                    state['cause'] = details.get('cause')
                    break
    
    return states
```

#### 1.2 Add IAM Permissions

Update `cfn/lambda-stack.yaml`:

```yaml
- Effect: Allow
  Action:
    - states:DescribeExecution
    - states:GetExecutionHistory
  Resource: !Sub 'arn:aws:states:${AWS::Region}:${AWS::AccountId}:execution:${ProjectName}-state-machine-${Environment}:*'
```

#### 1.3 Add STATE_MACHINE_ARN Environment Variable

Update `cfn/lambda-stack.yaml`:

```yaml
Environment:
  Variables:
    STATE_MACHINE_ARN: !GetAtt StepFunctionsStack.Outputs.StateMachineArn
```

---

### Phase 2: Frontend Components (Week 2)

#### 2.1 Create StepFunctionsVisualization Component

Create `frontend/src/components/StepFunctionsVisualization.tsx`:

```typescript
import React, { useEffect, useState } from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Box,
  Badge,
  ExpandableSection,
  ColumnLayout,
  Button,
  Alert
} from '@cloudscape-design/components';
import apiClient from '../services/api';

interface StepFunctionsState {
  name: string;
  type: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  enteredAt?: number;
  exitedAt?: number;
  duration?: number;
  input?: any;
  output?: any;
  error?: string;
  cause?: string;
}

interface StepFunctionsExecutionData {
  executionArn: string;
  status: string;
  currentState?: string;
  states: StepFunctionsState[];
  startDate: number;
  stopDate?: number;
}

interface Props {
  executionId: string;
  autoRefresh?: boolean;
}

export const StepFunctionsVisualization: React.FC<Props> = ({ 
  executionId, 
  autoRefresh = true 
}) => {
  const [data, setData] = useState<StepFunctionsExecutionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(true);

  const fetchStepFunctionsData = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      const response = await apiClient.get(`/executions/${executionId}/step-functions`);
      setData(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load Step Functions data');
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    fetchStepFunctionsData();
  }, [executionId]);

  // Auto-refresh for running executions
  useEffect(() => {
    if (!autoRefresh || !data || data.status !== 'RUNNING') return;

    const interval = setInterval(() => {
      fetchStepFunctionsData(true);
    }, 5000); // Refresh every 5 seconds

    return () => clearInterval(interval);
  }, [autoRefresh, data]);

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { color: any; label: string }> = {
      pending: { color: 'grey', label: 'Pending' },
      in_progress: { color: 'blue', label: 'In Progress' },
      completed: { color: 'green', label: 'Completed' },
      failed: { color: 'red', label: 'Failed' }
    };
    const config = statusMap[status] || { color: 'grey', label: status };
    return <Badge color={config.color}>{config.label}</Badge>;
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${minutes}m ${secs}s`;
  };

  const formatTimestamp = (timestamp: number): string => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  if (loading && !data) {
    return (
      <Container header={<Header variant="h3">Step Functions Orchestration</Header>}>
        <Box textAlign="center" padding="l">Loading orchestration data...</Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container header={<Header variant="h3">Step Functions Orchestration</Header>}>
        <Alert type="warning">{error}</Alert>
      </Container>
    );
  }

  if (!data) return null;

  return (
    <Container
      header={
        <Header
          variant="h3"
          actions={
            <Button
              iconName="refresh"
              onClick={() => fetchStepFunctionsData()}
              disabled={loading}
            >
              Refresh
            </Button>
          }
        >
          Step Functions Orchestration
        </Header>
      }
    >
      <SpaceBetween size="m">
        {/* Current State Indicator */}
        {data.currentState && (
          <Box>
            <SpaceBetween size="xs">
              <div style={{ fontSize: '12px', color: '#5f6b7a' }}>Current State</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Badge color="blue">{data.currentState}</Badge>
                <span style={{ fontSize: '14px', color: '#0972d3' }}>● Active</span>
              </div>
            </SpaceBetween>
          </Box>
        )}

        {/* State Timeline */}
        <ExpandableSection
          headerText={`State Timeline (${data.states.length} states)`}
          defaultExpanded={expanded}
          onChange={({ detail }) => setExpanded(detail.expanded)}
        >
          <SpaceBetween size="s">
            {data.states.map((state, index) => (
              <Box key={index} padding="s" variant="div">
                <SpaceBetween size="xs">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 600 }}>{state.name}</span>
                      {getStatusBadge(state.status)}
                      <Badge>{state.type}</Badge>
                    </div>
                    {state.duration !== undefined && (
                      <span style={{ fontSize: '12px', color: '#5f6b7a' }}>
                        {formatDuration(state.duration)}
                      </span>
                    )}
                  </div>

                  <ColumnLayout columns={3} variant="text-grid">
                    {state.enteredAt && (
                      <div>
                        <div style={{ fontSize: '11px', color: '#5f6b7a' }}>Entered</div>
                        <div style={{ fontSize: '12px' }}>{formatTimestamp(state.enteredAt)}</div>
                      </div>
                    )}
                    {state.exitedAt && (
                      <div>
                        <div style={{ fontSize: '11px', color: '#5f6b7a' }}>Exited</div>
                        <div style={{ fontSize: '12px' }}>{formatTimestamp(state.exitedAt)}</div>
                      </div>
                    )}
                    {state.duration !== undefined && (
                      <div>
                        <div style={{ fontSize: '11px', color: '#5f6b7a' }}>Duration</div>
                        <div style={{ fontSize: '12px' }}>{formatDuration(state.duration)}</div>
                      </div>
                    )}
                  </ColumnLayout>

                  {state.error && (
                    <Alert type="error" header={state.error}>
                      {state.cause}
                    </Alert>
                  )}

                  {/* Input/Output Details (collapsed by default) */}
                  {(state.input || state.output) && (
                    <ExpandableSection headerText="State Data" variant="footer">
                      <SpaceBetween size="s">
                        {state.input && (
                          <div>
                            <div style={{ fontSize: '11px', color: '#5f6b7a', marginBottom: '4px' }}>Input</div>
                            <pre style={{ 
                              fontSize: '11px', 
                              background: '#f2f3f3', 
                              padding: '8px', 
                              borderRadius: '4px',
                              overflow: 'auto',
                              maxHeight: '200px'
                            }}>
                              {typeof state.input === 'string' 
                                ? state.input 
                                : JSON.stringify(JSON.parse(state.input), null, 2)}
                            </pre>
                          </div>
                        )}
                        {state.output && (
                          <div>
                            <div style={{ fontSize: '11px', color: '#5f6b7a', marginBottom: '4px' }}>Output</div>
                            <pre style={{ 
                              fontSize: '11px', 
                              background: '#f2f3f3', 
                              padding: '8px', 
                              borderRadius: '4px',
                              overflow: 'auto',
                              maxHeight: '200px'
                            }}>
                              {typeof state.output === 'string' 
                                ? state.output 
                                : JSON.stringify(JSON.parse(state.output), null, 2)}
                            </pre>
                          </div>
                        )}
                      </SpaceBetween>
                    </ExpandableSection>
                  )}
                </SpaceBetween>
              </Box>
            ))}
          </SpaceBetween>
        </ExpandableSection>

        {/* CloudWatch Logs Link */}
        <Box textAlign="center">
          <Button
            iconName="external"
            href={`https://console.aws.amazon.com/states/home?region=${data.executionArn.split(':')[3]}#/executions/details/${data.executionArn}`}
            target="_blank"
          >
            View in Step Functions Console
          </Button>
        </Box>
      </SpaceBetween>
    </Container>
  );
};
```

#### 2.2 Integrate into ExecutionDetailsPage

Update `frontend/src/pages/ExecutionDetailsPage.tsx`:

```typescript
import { StepFunctionsVisualization } from '../components/StepFunctionsVisualization';

// Add after Wave Progress section
<StepFunctionsVisualization 
  executionId={execution.executionId}
  autoRefresh={execution.status === 'in_progress'}
/>
```

#### 2.3 Add API Client Method

Update `frontend/src/services/api.ts`:

```typescript
getExecutionStepFunctions: async (executionId: string) => {
  const response = await apiClient.get(`/executions/${executionId}/step-functions`);
  return response.data;
}
```

---

### Phase 3: Enhanced Visualization (Week 3 - Optional)

#### 3.1 State Diagram Visualization

Use a library like `react-flow` or `mermaid` to render the state machine diagram:

```typescript
import ReactFlow, { Node, Edge } from 'reactflow';
import 'reactflow/dist/style.css';

const StateMachineDiagram: React.FC<{ currentState?: string }> = ({ currentState }) => {
  const nodes: Node[] = [
    { id: '1', data: { label: 'InitiateWavePlan' }, position: { x: 250, y: 0 }, type: 'default' },
    { id: '2', data: { label: 'DetermineWavePlanState' }, position: { x: 250, y: 100 }, type: 'default' },
    // ... more nodes
  ];

  const edges: Edge[] = [
    { id: 'e1-2', source: '1', target: '2', animated: currentState === 'InitiateWavePlan' },
    // ... more edges
  ];

  return (
    <div style={{ height: '400px' }}>
      <ReactFlow nodes={nodes} edges={edges} fitView />
    </div>
  );
};
```

#### 3.2 Performance Metrics

Add metrics visualization:
- Average state duration
- Slowest states
- State transition frequency
- Error rate by state

---

## Testing Strategy

### Unit Tests

```python
# tests/python/unit/test_step_functions_api.py
def test_get_execution_step_functions_history():
    """Test Step Functions history endpoint"""
    pass

def test_transform_events_to_states():
    """Test event transformation logic"""
    events = [
        {'type': 'TaskStateEntered', 'timestamp': datetime.now(), 'stateEnteredEventDetails': {'name': 'InitiateWavePlan'}},
        {'type': 'TaskStateExited', 'timestamp': datetime.now(), 'stateExitedEventDetails': {'name': 'InitiateWavePlan'}}
    ]
    states = transform_events_to_states(events)
    assert len(states) == 1
    assert states[0]['name'] == 'InitiateWavePlan'
    assert states[0]['status'] == 'completed'
```

### Integration Tests

```python
# tests/python/integration/test_step_functions_visualization.py
def test_step_functions_api_integration():
    """Test complete flow: execution → Step Functions → API → frontend"""
    # Start execution
    # Wait for states to execute
    # Call API endpoint
    # Verify state timeline
    pass
```

### E2E Tests

```typescript
// tests/playwright/step-functions-visualization.spec.ts
test('should display Step Functions visualization', async ({ page }) => {
  await page.goto('/executions/test-execution-id');
  await expect(page.locator('text=Step Functions Orchestration')).toBeVisible();
  await expect(page.locator('text=Current State')).toBeVisible();
  await expect(page.locator('text=State Timeline')).toBeVisible();
});
```

---

## Deployment Checklist

- [ ] Add Step Functions history endpoint to `lambda/index.py`
- [ ] Add IAM permissions for `states:DescribeExecution` and `states:GetExecutionHistory`
- [ ] Add `STATE_MACHINE_ARN` environment variable to Lambda
- [ ] Create `StepFunctionsVisualization.tsx` component
- [ ] Integrate component into `ExecutionDetailsPage.tsx`
- [ ] Add API client method
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Write E2E tests
- [ ] Update documentation
- [ ] Deploy to dev environment
- [ ] Test with real executions
- [ ] Deploy to production

---

## Success Metrics

- **Visibility**: 100% of Step Functions states visible in UI
- **Performance**: State data loads in <2 seconds
- **Accuracy**: State timeline matches Step Functions console
- **Usability**: Users can diagnose issues 80% faster
- **Adoption**: 90% of users view Step Functions data during troubleshooting

---

## Insights from Archived Solution

The archived DR orchestration solution (`archive/dr-orchestration-artifacts/src/dashboards/`) provides valuable patterns:

### CloudWatch Logs Insights Integration

The archived solution used CloudWatch Logs Insights queries to track:
- **Lifecycle Phases**: instantiate, activate, replicate, cleanup
- **Resource Tracking**: resourceType, resourceName, RTO
- **Failure Analysis**: Parsed FailStateEntered events with detailed error context
- **Multi-Region Support**: Separate dashboards for us-east-1 and us-west-2

### Key Query Pattern

```sql
SOURCE '/aws/dr-orchestrator/stepfunctionfailures' 
| filter @message like /FailStateEntered/
| parse details.input '{"StatePayload":{"action":"*","resourceName":"*"}}' as action, resourceName
| display @timestamp, action, resourceName, error
| sort @timestamp desc
```

### Enhanced Implementation Recommendations

1. **Add CloudWatch Logs Widget**: Include Logs Insights queries in the visualization
2. **Failure State Parsing**: Parse and display detailed error context from failed states
3. **RTO Tracking**: Display time spent in each state vs expected RTO
4. **Lifecycle Phase Indicators**: Show which wave/phase is currently executing

## Future Enhancements

1. **CloudWatch Logs Integration**: Embedded Logs Insights queries for failure analysis
2. **State Machine Editor**: Visual editor for modifying state machine
3. **Execution Replay**: Replay failed executions with modified inputs
4. **Performance Analytics**: Historical analysis of state durations with RTO comparison
5. **Alerting**: Notifications when states take longer than expected
6. **Comparison View**: Compare multiple executions side-by-side
7. **Multi-Region Dashboard**: Consolidated view across all regions

---

## References

- [AWS Step Functions GetExecutionHistory API](https://docs.aws.amazon.com/step-functions/latest/apireference/API_GetExecutionHistory.html)
- [Step Functions Event History](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-examine-history.html)
- [React Flow Documentation](https://reactflow.dev/)
- [CloudScape Design System](https://cloudscape.design/)
