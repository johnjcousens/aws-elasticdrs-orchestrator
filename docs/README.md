# AWS DRS Orchestration - Documentation

## Current Active Documentation

### Core Project Documents
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current project status, roadmap, and session history
- **[MASTER_IMPLEMENTATION_ROADMAP.md](MASTER_IMPLEMENTATION_ROADMAP.md)** - Overall implementation plan
- **[MVP_COMPLETION_PLAN.md](MVP_COMPLETION_PLAN.md)** - MVP phase completion plan

### Deployment & Operations
- **[LAMBDA_DEPLOYMENT_GUIDE.md](LAMBDA_DEPLOYMENT_GUIDE.md)** - Lambda deployment procedures
- **[AWS_DRS_OPERATIONAL_RULES_AND_CONSTRAINTS.md](AWS_DRS_OPERATIONAL_RULES_AND_CONSTRAINTS.md)** - AWS DRS operational guidelines
- **[DRS_API_COMPREHENSIVE_ANALYSIS.md](DRS_API_COMPREHENSIVE_ANALYSIS.md)** - DRS API documentation

### Implementation Guides
- **[CUSTOM_TAGS_IMPLEMENTATION_STATUS.md](CUSTOM_TAGS_IMPLEMENTATION_STATUS.md)** - Custom tags implementation (Session 61)
- **[IAM_FIX_APPLIED.md](IAM_FIX_APPLIED.md)** - IAM permissions fix documentation
- **[DRS_EXECUTION_FIX_IMPLEMENTATION_PLAN.md](DRS_EXECUTION_FIX_IMPLEMENTATION_PLAN.md)** - Execution fix plan

### Architecture & Design
- **[STEP_FUNCTIONS_DESIGN_PLAN.md](STEP_FUNCTIONS_DESIGN_PLAN.md)** - Step Functions integration plan
- **[JOB_LOG_EVENT_TRACKING_ROADMAP.md](JOB_LOG_EVENT_TRACKING_ROADMAP.md)** - Event tracking roadmap
- **[PHASE_3_ENTERPRISE_ENHANCEMENTS_GUIDE.md](PHASE_3_ENTERPRISE_ENHANCEMENTS_GUIDE.md)** - Phase 3 enhancements

### Analysis & Planning
- **[AWS_DRS_ORCHESTRATION_TCO_ANALYSIS_FIXED.md](AWS_DRS_ORCHESTRATION_TCO_ANALYSIS_FIXED.md)** - TCO analysis
- **[API_GATEWAY_AUTH_INVESTIGATION.md](API_GATEWAY_AUTH_INVESTIGATION.md)** - API Gateway auth investigation

## Subdirectories

### `/requirements/`
Business requirements and specifications

### `/architecture/`
System architecture diagrams and documentation

### `/guides/`
User guides and operational procedures

### `/competitive-analysis/`
Competitive analysis and market research

### `/presentations/`
Project presentations and demos

## Archive (Local Only - Not in Git)

Historical documents are preserved locally in `docs/archive/` but excluded from git to keep the repository clean.

### Archive Structure
- **`archive/sessions/`** - Historical development sessions (SESSION_55-61, etc.)
- **`archive/bugs/`** - Resolved bug investigations (BUG_2 through BUG_12)
- **`archive/investigations/`** - Historical troubleshooting (DRILL_*, CRITICAL_FINDING_*, etc.)
- **`archive/deprecated/`** - Superseded implementation plans and old documentation

### Why Archive is Local Only
- Keeps git repo clean and focused on current work
- Preserves complete project history locally for reference
- Reduces cognitive load when browsing project
- Historical context available when needed without cluttering workspace

### Accessing Archive
All archived documents remain on your local filesystem at `docs/archive/`. They are simply excluded from git tracking via `.gitignore`.

## Documentation Standards

### File Naming
- Use descriptive, uppercase names with underscores
- Include version/date in filename when appropriate
- Prefix with category (BUG_, SESSION_, etc.)

### Status Indicators
- ✅ Completed/Working
- 🚧 In Progress
- ⏳ Planned
- ❌ Failed/Deprecated

### Updates
- Always update PROJECT_STATUS.md when completing major milestones
- Document deployment results and validation
- Create session summaries for significant work

## Quick Links

### Most Referenced
1. [PROJECT_STATUS.md](PROJECT_STATUS.md) - Always start here
2. [LAMBDA_DEPLOYMENT_GUIDE.md](LAMBDA_DEPLOYMENT_GUIDE.md) - For deployments
3. [AWS_DRS_OPERATIONAL_RULES_AND_CONSTRAINTS.md](AWS_DRS_OPERATIONAL_RULES_AND_CONSTRAINTS.md) - For DRS operations

### Latest Work
- Session 61: Launch Config Validation + Custom Tags Implementation
- Session 60: Cognito User Extraction
- Session 59: Drill Success Resolution

---

**Last Updated**: November 30, 2025  
**Repository**: AWS-DRS-Orchestration  
**Status**: MVP Phase 1-2 Complete, Phase 3 Planning
