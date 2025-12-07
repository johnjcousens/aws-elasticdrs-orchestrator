# Product Overview

## AWS DRS Orchestration Solution

A comprehensive serverless disaster recovery orchestration platform that provides VMware Site Recovery Manager (SRM) parity for AWS Elastic Disaster Recovery Service (DRS).

### Core Purpose

Enable enterprise organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, and automated health checks - matching or exceeding VMware SRM capabilities while leveraging AWS-native services for superior reliability, scalability, and cost-effectiveness.

### Key Features

#### Protection Groups Management
- **Automatic Server Discovery**: Real-time DRS source server discovery by AWS region (13 regions supported)
- **VMware SRM-Like Experience**: Visual server selection with assignment status indicators
- **Single Server Per Group**: Conflict prevention - each server can only belong to one Protection Group
- **Server Deselection**: Edit Protection Groups and remove servers as needed
- **Real-Time Search**: Filter servers by hostname, Server ID, or Protection Group name
- **Auto-Refresh**: Silent 30-second auto-refresh for up-to-date server status
- **Assignment Tracking**: Visual badges show which servers are available vs. assigned

#### Recovery Plans
- **Wave-Based Orchestration**: Define multi-wave recovery sequences with unlimited flexibility (vs VMware SRM's 5 fixed priorities)
- **Automation Actions**: Pre-wave and post-wave SSM automation for health checks
- **Dependency Management**: Automatic wave dependency handling and validation
- **Cross-Account Support**: Execute recovery across multiple AWS accounts
- **Drill Mode**: Test recovery procedures without impacting production

#### Execution Monitoring
- **Real-time Dashboard**: Live execution progress with wave status
- **Execution History**: Complete audit trail of all recovery executions
- **CloudWatch Integration**: Deep-link to CloudWatch Logs for troubleshooting
- **Wave Progress**: CloudScape Wizard/Stepper timeline showing recovery progress

#### API-First Architecture
- **Complete REST API**: Every operation available through RESTful API
- **Cognito Authentication**: JWT token-based authentication
- **DevOps Integration**: Enable CI/CD pipeline integration and automation
- **Rate Limiting**: 500 burst, 1000 sustained requests/second

### Target Users & Personas

#### Primary: DR Administrator (Sarah Martinez)
- **Role**: Senior DR Administrator with 5+ years VMware SRM experience
- **Goals**: Automate recovery plan execution, reduce manual effort, achieve sub-5-minute RTO
- **Pain Points**: Manual server discovery, limited to 5 priority levels, expensive storage array replication
- **Success Criteria**: Create Protection Groups in <5 minutes, execute drills without production impact, 99.9% recovery success rate

#### Secondary: DevOps Engineer (Alex Chen)
- **Role**: Senior DevOps Engineer
- **Goals**: Integrate DR automation into CI/CD pipelines, automate pre/post-recovery validation
- **Needs**: RESTful API, CloudWatch integration, Git-based configuration management

#### Tertiary: IT Manager (James Wilson)
- **Role**: IT Infrastructure Manager
- **Goals**: Demonstrate compliance, optimize costs, ensure business continuity
- **Needs**: Execution history, cost reporting, success metrics, executive-level status reporting

### Business Value

#### Cost Efficiency
- **Operational Cost**: $12-40/month vs $10K-50K/year VMware SRM licensing (80%+ reduction)
- **Pay-Per-Use**: Cloud-native pricing model vs CapEx requirements
- **No Storage Array Licenses**: Eliminates expensive replication licensing

#### Technical Advantages
- **Platform Flexibility**: Agent-based replication supports any source platform (VMware, physical, cloud VMs)
- **Sub-Second RPO**: Continuous block-level replication vs traditional storage-array limitations
- **Unlimited Orchestration**: Wave-based execution with explicit dependencies (no artificial constraints)
- **Cloud-Native**: AWS-managed infrastructure eliminating operational overhead
- **Serverless Architecture**: Scales automatically, no infrastructure management

#### Strategic Benefits
- Enables seamless VMware to AWS disaster recovery transitions
- Supports multi-cloud and hybrid cloud DR strategies
- Provides complete audit trails for compliance
- Scales from small deployments to enterprise-wide implementations

### Current Status

**Phase 1 Complete**: Core orchestration infrastructure operational
- ✅ Protection Groups CRUD with automatic server discovery
- ✅ Recovery Plans with wave-based orchestration
- ✅ Execution Engine with Step Functions integration
- ✅ Modern React UI with AWS CloudScape Design System
- ✅ Complete REST API with Cognito authentication

**Phase 2 Complete**: Polling infrastructure operational
- ✅ StatusIndex GSI deployed and operational
- ✅ ExecutionFinder Lambda (EventBridge scheduled)
- ✅ ExecutionPoller Lambda (adaptive polling)
- ✅ Performance validated (exceeds all targets)

**Phase 3 Complete**: CloudScape Migration (100%)
- ✅ All 27 migration tasks completed
- ✅ Material-UI fully replaced with CloudScape
- ✅ AWS Console-native look and feel

**Current Focus**: DRS integration validation
- ✅ Authentication issues resolved (Session 68)
- ⚠️ ec2:DetachVolume permission fix applied (Session 69)
- ⚠️ Awaiting DRS drill validation with both servers

**Deployment**: 
- **Frontend**: https://d1wfyuosowt0hl.cloudfront.net (CloudFront Distribution E46O075T9AHF3)
- **API**: https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test
- **Environment**: TEST (us-east-1, account 438465159935)
- **Test User**: testuser@example.com / IiG2b1o+D$

### Success Metrics

#### Operational Metrics
- **Recovery Time Objective (RTO)**: <15 minutes for critical applications
- **Recovery Point Objective (RPO)**: <5 minutes (leveraging DRS sub-second replication)
- **Recovery Success Rate**: >99.5%
- **API Availability**: >99.9%

#### Cost Metrics
- **Monthly Operational Cost**: $12-40/month (target: <$50/month)
- **Cost Per Protected Server**: <$0.50/month/server
- **Total Cost Reduction vs SRM**: >80%

#### User Satisfaction Metrics
- **Time to Create Protection Group**: <5 minutes
- **Time to Create Recovery Plan**: <10 minutes
- **DR Test Execution Time**: <30 minutes for 3-tier application
- **User Satisfaction Score**: >4.5/5.0
