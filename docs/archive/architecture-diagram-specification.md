# AWS DRS Orchestration Architecture Diagram Specification
# For use with draw.io (diagrams.net)

## Diagram Title
**AWS DRS Orchestration System - Complete Architecture**

## Component Layout (7 Horizontal Layers)

### Layer 1: Users & Presentation (Top)
**Background**: Light Orange (#FFE6CC)

Components:
- Actor Icon: "DR Administrator" (left)
- Actor Icon: "DevOps Engineer" (center-left)
- CloudFront (Orange #FF9900): "Global CDN, HTTPS Only, OAI"
- S3 Bucket (Green #3F8624): "React 18.3 SPA, Material-UI 6, Static Assets"

Connections:
- Users → CloudFront (HTTPS)
- CloudFront → S3 (OAI)

---

### Layer 2: Security & API Gateway
**Background**: Light Blue (#E1F5FE)

Components:
- AWS WAF (Red #DD344C): "Rate Limiting, IP Filtering, SQL Injection Protection"
- Cognito User Pool (Red #DD344C): "JWT Auth, User Management, MFA Optional"
- API Gateway (Purple #7B68EE): "REST API, 30+ Resources, Cognito Authorizer"

Connections:
- Users → Cognito (Authentication)
- CloudFront → WAF → API Gateway
- API Gateway ← Cognito (Token Validation)

---

### Layer 3: Business Logic (Lambda Functions)
**Background**: Light Gray (#F5F5F5)

Components:
- Lambda: API Handler (Orange #FF9900): 
  * "Python 3.12"
  * "912 lines"
  * "CRUD Operations"
  * "Validation"
  * "Case Transformation"
  
- Lambda: Orchestration (Orange #FF9900):
  * "Python 3.12"
  * "556 lines"
  * "DRS Integration"
  * "Job Monitoring"
  * "Health Checks"

Connections:
- API Gateway → API Handler Lambda (Sync Invoke)
- API Handler → Orchestration Lambda (via Step Functions)

---

### Layer 4: Orchestration Engine
**Background**: Light Purple (#F3E5F5)

Components:
- Step Functions State Machine (Purple #7B68EE):
  * "35+ States"
  * "Wave-Based Execution"
  * "Sequential/Parallel"
  * "Error Retry Logic"
  * "Max 1 hour timeout"

Connections:
- API Handler Lambda → Step Functions (StartExecution)
- Step Functions → Orchestration Lambda (Invoke per wave)

---

### Layer 5: Data Storage (DynamoDB)
**Background**: Light Gray (#E0E0E0)

Components:
- DynamoDB: Protection Groups (Blue #4682B4):
  * "PK: Id (UUID)"
  * "Attributes: Name, Region, ServerIds"
  * "On-Demand Capacity"
  * "Encryption: SSE"
  
- DynamoDB: Recovery Plans (Blue #4682B4):
  * "PK: PlanId (UUID)"
  * "Attributes: Name, ProtectionGroupIds, Waves"
  * "On-Demand Capacity"
  * "Encryption: SSE"
  
- DynamoDB: Execution History (Blue #4682B4):
  * "PK: ExecutionId (UUID)"
  * "Attributes: Status, WaveStatus, StartTime"
  * "On-Demand Capacity"
  * "Encryption: SSE"

Connections:
- API Handler Lambda ↔ All 3 DynamoDB tables (Read/Write)
- Orchestration Lambda → Execution History (Write only)

---

### Layer 6: AWS Integration Services
**Background**: Light Yellow (#FFFACD)

Components:
- AWS DRS (Orange #FF9900):
  * "DescribeSourceServers"
  * "StartRecovery"
  * "DescribeJobs"
  * "TerminateRecoveryInstances"
  
- Amazon EC2 (Orange #FF9900):
  * "DescribeInstances"
  * "DescribeInstanceStatus"
  * "Health Checks"
  
- Amazon SNS (Red #DD344C):
  * "Execution Notifications"
  * "Email/Webhook"

Connections:
- Orchestration Lambda → AWS DRS (boto3)
- Orchestration Lambda → EC2 (boto3)
- Orchestration Lambda → SNS (boto3)

---

### Layer 7: Monitoring & Audit (Bottom)
**Background**: Light Green (#E8F5E9)

Components:
- CloudWatch Logs (Red #DD344C):
  * "Lambda Logs"
  * "API Gateway Logs"
  * "Retention: 7-90 days"
  
- CloudWatch Metrics (Red #DD344C):
  * "Custom Metrics"
  * "Lambda Duration"
  * "API Latency"
  
- CloudWatch Alarms (Red #DD344C):
  * "Error Rate > 5%"
  * "Execution Failures"
  * "SNS Notifications"
  
- CloudTrail (Blue #4682B4):
  * "API Audit Trail"
  * "90 Days Retention"
  * "S3 Archive"

Connections:
- All Lambda functions → CloudWatch Logs
- API Gateway → CloudWatch Metrics
- All services → CloudTrail (automatic)

---

## Data Flow: Recovery Execution (Main Use Case)

```
User → CloudFront → API Gateway → Lambda (API Handler)
  ↓
  DynamoDB: Get Recovery Plan
  ↓
  Step Functions: StartExecution
  ↓
  Step Functions invokes Orchestration Lambda per wave:
    ↓
    Wave 1: Database Tier
      → DRS: StartRecovery (s-db1, s-db2)
      → DRS: DescribeJobs (poll until COMPLETED)
      → EC2: DescribeInstanceStatus (health check)
      → DynamoDB: Update wave status
      → Wait 60 seconds
    ↓
    Wave 2: Application Tier
      → DRS: StartRecovery (s-app1, s-app2, s-app3)
      → DRS: DescribeJobs (poll until COMPLETED)
      → EC2: DescribeInstanceStatus (health check)
      → DynamoDB: Update wave status
      → Wait 30 seconds
    ↓
    Wave 3: Web Tier
      → DRS: StartRecovery (s-web1, s-web2)
      → DRS: DescribeJobs (poll until COMPLETED)
      → EC2: DescribeInstanceStatus (health check)
      → DynamoDB: Update wave status
  ↓
  DynamoDB: Mark execution COMPLETED
  ↓
  SNS: Send notification
  ↓
  User receives email: "Recovery complete"
```

---

## Multi-Account Architecture (Optional Side Panel)

### Hub Account (Orchestration)
- All components from Layers 1-7 above

### Spoke Account 1 (Production)
- AWS DRS
- EC2 Instances (source servers)
- IAM Role: DRS-Orchestration-Role
  * Trust: Hub Account Lambda Role
  * Permissions: DRS + EC2 read/write

### Spoke Account 2 (DR Site)
- AWS DRS
- EC2 Instances (recovery targets)
- IAM Role: DRS-Orchestration-Role
  * Trust: Hub Account Lambda Role
  * Permissions: DRS + EC2 read/write

**Cross-Account Flow**:
```
Hub Lambda → STS AssumeRole → Spoke IAM Role → DRS/EC2 APIs
```

---

## Color Legend

- **Orange (#FF9900)**: AWS Compute (Lambda, DRS, CloudFront)
- **Purple (#7B68EE)**: AWS Integration (API Gateway, Step Functions)
- **Blue (#4682B4)**: AWS Storage (DynamoDB, CloudTrail, S3)
- **Red (#DD344C)**: AWS Security (Cognito, WAF, SNS, CloudWatch)
- **Green (#3F8624)**: Data/Content (S3 frontend assets)
- **Gray (#232F3E)**: Users/Actors

---

## Key Annotations to Add

1. **API Gateway**: "30+ resources, Cognito authorizer, 500 burst limit"
2. **Lambda API Handler**: "912 lines Python, CRUD + validation"
3. **Lambda Orchestration**: "556 lines Python, DRS integration"
4. **Step Functions**: "35+ states, wave-based, retry logic"
5. **DynamoDB**: "On-demand, auto-scaling, 3 tables"
6. **CloudFront**: "Global CDN, HTTPS only, OAI to S3"
7. **Cognito**: "JWT tokens, 1hr access, 30d refresh"
8. **DRS Integration**: "4 APIs: Describe, Start, Monitor, Terminate"

---

## Drawing Instructions for draw.io

1. **Create file**: New Diagram → AWS Architecture → Blank
2. **Enable AWS shape library**: More Shapes → AWS 19 → Select all → Apply
3. **Create layers** (top to bottom):
   - Add rectangles with rounded corners for each layer
   - Use colors from legend above
   - Add layer title in bold
4. **Add AWS icons**:
   - Drag from AWS library (CloudFront, Lambda, DynamoDB, etc.)
   - Size: ~80x80 pixels per icon
   - Add labels below each icon
5. **Add connections**:
   - Use arrows with labels (HTTP, boto3, etc.)
   - Style: Orthogonal routing
   - Color: Black with 2px width
6. **Add annotations**:
   - Use text boxes for technical details
   - Font: 10pt regular, gray text
7. **Layout**:
   - Total size: 1600x1400 pixels
   - Margins: 40px all sides
   - Spacing between layers: 20px
   - Spacing between components: 40px

---

## Export Options

1. **For documentation**: Export as PNG (300 DPI, transparent background)
2. **For presentations**: Export as SVG (vector, scalable)
3. **For editing**: Save as .drawio (editable XML format)

---

**Created**: November 12, 2025 - 9:15 PM EST  
**Based on**: ARCHITECTURAL_DESIGN_DOCUMENT.md  
**Tool**: draw.io (diagrams.net)  
**Version**: 1.0
