---
inclusion: manual
---

# AWS Well-Architected DevOps Guidance

## Document Overview

Structured approach for organizations to cultivate high-velocity, security-focused culture using modern technologies and DevOps best practices.

## DevOps Sagas (Core Domains)

1. **Organizational Adoption**: Customer-centric, adaptive culture
2. **Development Lifecycle**: Develop, review, deploy swiftly and securely
3. **Quality Assurance**: Test-first methodology integrated into development
4. **Automated Governance**: Directive, detective, preventive, responsive measures
5. **Observability**: Detect and address issues through monitoring

## Organizational Adoption

### Leader Sponsorship
- Appoint single-threaded leader for DevOps adoption
- Align DevOps adoption with business objectives
- Drive improvement through regular business reviews and KPIs
- Create cross-functional enabling team

### Team Topologies
- **Stream-aligned**: Deliver value to customers by focusing on specific products
- **Platform**: Create and maintain shared infrastructure and tools
- **Enabling**: Provide just-in-time skills and expertise
- **Complicated subsystem**: Specialized subsystems requiring deep domain knowledge

### Team Dynamics
- Prioritize shared accountability over individual achievements
- Structure teams around desired business outcomes (Conway's Law)
- Provide teams ownership of entire value stream
- Keep team sizes manageable (7±2 individuals)

## Development Lifecycle

### Local Development
- Establish consistent development environments
- Commit local changes early and often
- Enforce security checks before commit
- Enforce coding standards before commit

### Software Component Management
- Use version control with appropriate access management
- Keep feature branches short-lived
- Use artifact repositories with enforced authentication
- Maintain approved open-source software license list
- Generate comprehensive software inventory for each build

### Everything as Code
- Organize infrastructure as code for scale
- Codify data operations
- Integrate documentation into development lifecycle
- Automate compute image generation and distribution

### Code Review
- Standardize coding practices
- Perform peer review for code changes
- Establish clear completion criteria
- Foster constructive and inclusive review culture
- Create consistent commit messages using specification

### Continuous Integration
- Integrate code changes regularly and frequently
- Trigger builds automatically upon source code modifications
- Ensure automated quality assurance for every build
- Provide consistent, actionable feedback to developers

### Continuous Delivery
- Deploy changes to production frequently
- Deploy exclusively from trusted artifact repositories
- Integrate quality assurance into deployments
- Automate the entire deployment process

## Quality Assurance

### Functional Testing
- Unit tests for individual component functionality
- Integration tests for system interactions and data flows
- Acceptance tests for end-user experience

### Non-functional Testing
- Static testing for code quality
- Performance testing for system reliability
- Resilience testing for recovery preparedness
- Contract testing for service integrations

### Security Testing
- Static application security testing (SAST)
- Dynamic application security testing (DAST)
- Software composition analysis for third-party components
- Proactive exploratory security testing

## Automated Governance

### Secure Access
- Centralize and federate access with temporary credential vending
- Treat pipelines as production resources
- Limit human access with just-in-time access
- Implement break-glass procedures
- Adopt zero trust security model

### Data Lifecycle Management
- Define recovery objectives for business continuity
- Strengthen security with systematic encryption
- Automate data processes using pipelines
- Maintain data compliance with classification strategies

### Compliance and Guardrails
- Adopt risk-based compliance framework
- Automate deployment of detective controls
- Implement preventative guardrails
- Auto-remediate non-compliant findings

## Observability

### Strategic Instrumentation
- Center observability around business and technical outcomes
- Centralize tooling for telemetry data interpretation
- Instrument all systems for comprehensive data collection
- Build health checks into every service
- Set and monitor service level objectives

### Data Ingestion
- Aggregate logs and events across workloads
- Centralize logs for security investigations
- Implement distributed tracing for request tracking
- Aggregate health and status metrics

### Continuous Monitoring
- Automate alerts for security and performance issues
- Conduct post-incident analysis for improvement
- Report on business metrics for data-driven decisions
- Visualize telemetry data in real-time
- Optimize alerts to prevent fatigue

## Key Concepts

### You Build It, You Run It
Team responsible for building a system is also responsible for running, maintaining, and owning it.

### Guardian Model
Embed specialized champions within teams to scale centralized functions (security, quality, audit).

### Two-Pizza Teams
Small, autonomous teams with single-threaded focus that minimize handoffs.
