# Documentation Archive

This directory contains historical project documentation that is preserved locally but excluded from git tracking.

## Purpose

The archive maintains a complete project history while keeping the git repository clean and focused on current work. All files here remain on your local filesystem but are not pushed to the remote repository.

## Archive Structure

### `/sessions/` - Development Sessions
Historical session documentation tracking major development work:
- SESSION_55_HANDOFF.md
- SESSION_57_PART_9 through PART_17 (Frontend UI fixes)
- SESSION_60_DEPLOYMENT_COMPLETE.md
- SESSION_61_DEPLOYMENT_VALIDATION.md
- And other session tracking documents

**Use Case**: Reference past debugging approaches, understand evolution of solutions, track when features were implemented.

### `/bugs/` - Bug Investigations
Resolved bug analysis and resolution documentation:
- BUG_2 through BUG_12 investigations
- Root cause analyses
- Resolution documentation
- Implementation plans for fixes

**Use Case**: Understand why certain design decisions were made, reference similar issues, learn from past troubleshooting approaches.

### `/investigations/` - Historical Troubleshooting
Drill failures, conversion issues, and other technical investigations:
- DRILL_FAILURE_* files
- DRILL_SUCCESS_* files
- DRILL_CONVERSION_* files
- CRITICAL_FINDING_* files
- CONVERSION_SERVER_* files

**Use Case**: Reference troubleshooting methodologies, understand system behavior patterns, avoid repeating failed approaches.

### `/deprecated/` - Superseded Documentation
Old implementation plans and documentation replaced by newer versions:
- ROLLBACK_* files
- Old implementation plans
- Superseded analysis documents
- Deprecated test scenarios

**Use Case**: Understand project evolution, see why approaches were changed, reference historical decisions.

## Why Local Only?

### Benefits of Archiving
1. **Clean Repository** - Git repo focuses on current, actionable documentation
2. **Complete History** - Nothing is lost, everything preserved locally
3. **Reduced Cognitive Load** - Easier to find current documentation
4. **Faster Cloning** - New developers get lean, focused repo
5. **Better Organization** - Clear separation of active vs. historical docs

### Git Configuration
These directories are excluded via `.gitignore`:
```gitignore
docs/archive/sessions/
docs/archive/bugs/
docs/archive/investigations/
docs/archive/deprecated/
```

## Accessing Archived Content

All archived files remain in your local workspace at:
```
AWS-DRS-Orchestration/docs/archive/
```

Use standard file system tools to access:
```bash
# List all sessions
ls -la docs/archive/sessions/

# Search for specific content
grep -r "keyword" docs/archive/

# View specific archived file
code docs/archive/sessions/SESSION_61_DEPLOYMENT_VALIDATION.md
```

## When to Archive

Archive documentation when:
- ✅ Bug is resolved and documented in PROJECT_STATUS.md
- ✅ Session work is complete and summarized
- ✅ Investigation is concluded with findings documented
- ✅ Implementation plan is superseded by newer version
- ✅ File is no longer referenced in active work

Keep documentation active when:
- ❌ Still actively referenced in current work
- ❌ Contains operational procedures
- ❌ Part of system architecture documentation
- ❌ Required for understanding current implementation

## Maintenance

### Periodic Review
Every few months, review archived content:
1. Verify old sessions still provide value
2. Consider consolidating related investigations
3. Extract lessons learned into permanent guides
4. Delete truly obsolete content if needed

### Don't Archive
Never archive these categories:
- Current project status (PROJECT_STATUS.md)
- Active implementation guides
- System architecture documentation
- Operational procedures and runbooks
- Deployment guides
- API documentation

## Questions?

If unsure whether to archive a document:
1. Is it currently referenced in PROJECT_STATUS.md? → Keep active
2. Does it describe current system behavior? → Keep active
3. Is it historical troubleshooting/debugging? → Archive
4. Is it superseded by a newer version? → Archive

---

**Archive Created**: November 30, 2025  
**Total Archived**: 60+ historical documents  
**Status**: Active - Local filesystem only, excluded from git
