---
inclusion: manual
---

# AWS Migration Lens

## Document Overview

Best practices for migrating on-premises or hybrid workloads to AWS, combining migration phases (assess, mobilize, migrate/modernize) with the six Well-Architected pillars.

## Migration Strategies (7 Rs)

1. **Retire**: Shut down applications no longer needed
2. **Retain**: Keep in source environment if not ready to migrate
3. **Rehost**: Move without changes (lift and shift)
4. **Relocate**: Transfer servers in bulk to cloud version
5. **Repurchase**: Replace with different version or product
6. **Replatform**: Move with some optimization
7. **Refactor**: Modify architecture to leverage cloud-native features

## Design Principles

1. Create a clear vision for the journey
2. Get leadership support early
3. Understand the AWS environment
4. Define migration scope
5. Know your applications
6. Get application owners' buy-in early
7. Understand application requirements
8. Align with governance and compliance frameworks
9. Maintain operations during migration
10. Create migration plans (waves)

## Operational Excellence

### Assess Phase
- Base migration plans on up-to-date discovery data
- Refresh data regularly for long-running migrations

### Mobilize Phase
- Define and measure KPIs aligned with business outcomes
- Assess team skills and implement training plans
- Establish a Cloud Center of Excellence (CCoE)
- Calculate migration velocity considering technical and non-technical factors

### Migrate Phase
- Implement testing phase strategy
- Review CI/CD pipeline
- Provision resources through Infrastructure as Code

## Security

### Assess Phase
- Review security aspects of discovery tools
- Map existing security tools to AWS equivalents
- Establish compliance frameworks

### Mobilize Phase
- Implement strong identity and least privilege
- Build AWS environment following security foundations
- Establish secure connectivity between on-premises and AWS
- Define policies for data encryption at rest

### Migrate Phase
- Review security of migration tools
- Implement detection and investigation capabilities
- Establish incident response capabilities

## Reliability

### Assess Phase
- Define SLAs across all applications and environments
- Define and automate runbooks
- Map AWS Global Infrastructure to business SLAs
- Define RPO and RTO targets
- Select disaster recovery strategy

### Mobilize Phase
- Review service quotas and constraints
- Plan network topology for migration
- Ensure sufficient bandwidth for traffic and data replication
- Implement highly available links to on-premises
- Design networks to prevent IP address conflicts

### Migrate Phase
- Test high availability, fault tolerance, and disaster recovery

## Performance Efficiency

### Assess Phase
- Evaluate performance requirements for workloads
- Find efficient data transfer methods
- Select optimal storage options
- Identify network requirements

### Mobilize Phase
- Set up metrics for performance monitoring
- Select best-performing cloud infrastructure that can scale
- Benchmark existing workloads

### Migrate Phase
- Perform stress and user acceptance tests
- Perform Well-Architected Reviews after each iteration
- Monitor performance through all migration phases

## Cost Optimization

### Assess Phase
- Assess existing infrastructure usage and dependencies
- Leverage AWS programs designed to accelerate migrations

### Mobilize Phase
- Use automation efficiently for migration
- Minimize applications and data to be migrated
- Right-size replication servers
- Define cost allocation strategy

### Migrate Phase
- Monitor spend with budgeting and forecasting tools
- Use AWS Cost Anomaly Detection
- Select right purchase options and scalable architecture

## Migration Planning

### Discovery and Assessment
- Use discovery tools for comprehensive environment data
- Understand application dependencies for wave planning
- Collect fine-grained infrastructure usage data
- Gather data with frequent samples over at least two weeks

### Migration Waves
- Split migration into smaller units (4-8 week periods)
- Calculate potential migration velocity
- Consider network bandwidth, team availability, change freezes
- Test migration windows and impact
- Plan for failure and establish rollback procedures

### Cutover Planning
- Estimate required maintenance windows
- Test migration activities to validate completion time
- Define communication channels and intervals
- Determine data synchronization approach for rollbacks

## DRS-Specific Considerations

### AWS Elastic Disaster Recovery
- Configure replication settings based on RPO requirements
- Use dedicated replication subnets
- Monitor replication lag and data backlog metrics
- Test recovery procedures using drill mode
- Document recovery runbooks

### Recovery Objectives
- **RPO (Recovery Point Objective)**: Maximum acceptable data loss
- **RTO (Recovery Time Objective)**: Maximum acceptable downtime
- Design DR strategy based on business requirements
