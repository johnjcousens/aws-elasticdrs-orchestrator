# Developer Onboarding Checklist

This checklist ensures new developers can quickly set up their development environment for the AWS DRS Orchestration project with proper Python coding standards.

## Prerequisites Setup

### System Requirements
- [ ] **Python 3.12** installed and accessible via `python3 --version`
- [ ] **Git** installed and configured with your credentials
- [ ] **AWS CLI** installed and configured with appropriate credentials
- [ ] **Node.js 18+** installed (for frontend development)
- [ ] **IDE** installed (VS Code or PyCharm Professional recommended)

### AWS Access
- [ ] AWS account access with appropriate permissions
- [ ] AWS CLI configured: `aws sts get-caller-identity` works
- [ ] Access to DRS service in target regions
- [ ] S3 bucket access for deployment artifacts

## Project Setup

### Repository Clone
- [ ] Clone repository: `git clone <repository-url>`
- [ ] Navigate to project directory: `cd aws-drs-orchestration`
- [ ] Verify project structure matches documentation

### Python Environment
- [ ] Create virtual environment: `python3 -m venv venv`
- [ ] Activate virtual environment:
  - Linux/macOS: `source venv/bin/activate`
  - Windows: `venv\Scripts\activate`
- [ ] Upgrade pip: `pip install --upgrade pip`
- [ ] Install development dependencies: `pip install -r requirements-dev.txt`
- [ ] Verify tools installation:
  - [ ] `black --version` (code formatter)
  - [ ] `flake8 --version` (linter)
  - [ ] `isort --version` (import sorter)
  - [ ] `pytest --version` (test runner)

### Frontend Environment (if working on UI)
- [ ] Navigate to frontend: `cd frontend`
- [ ] Install dependencies: `npm install`
- [ ] Verify build works: `npm run build`
- [ ] Return to project root: `cd ..`

## IDE Configuration

### VS Code Setup
- [ ] Install recommended extensions (see `.vscode/extensions.json`)
- [ ] Verify settings are loaded from `.vscode/settings.json`
- [ ] Test code formatting: Open Python file, save, verify Black formatting applied
- [ ] Test linting: Create PEP 8 violation, verify Flake8 shows error
- [ ] Test import sorting: Mess up imports, save, verify isort fixes them
- [ ] Test debugging: Run debug configuration for Lambda function

### PyCharm Setup (Alternative)
- [ ] Follow [PyCharm Setup Guide](pycharm-setup.md)
- [ ] Configure project interpreter to use virtual environment
- [ ] Set up Black, Flake8, and isort integration
- [ ] Test all integrations work correctly

## Code Quality Tools

### Pre-commit Hooks (Optional - Corporate Limitation)
- [ ] Try installing pre-commit: `pre-commit install`
- [ ] If successful, test with dummy commit
- [ ] If fails (corporate git defender), note limitation and proceed

### Manual Quality Checks
- [ ] Run Black on sample file: `black lambda/index.py --diff`
- [ ] Run Flake8 on sample file: `flake8 lambda/index.py`
- [ ] Run isort on sample file: `isort lambda/index.py --diff`
- [ ] Run tests: `pytest tests/ -v`

### Quality Report Generation
- [ ] Generate quality report: `python scripts/generate_quality_report.py`
- [ ] Review HTML report in browser
- [ ] Understand baseline violations concept

## Development Workflow

### Code Changes
- [ ] Create feature branch: `git checkout -b feature/your-feature`
- [ ] Make code changes following PEP 8 standards
- [ ] Run quality checks before committing:
  - [ ] `black .` (format all files)
  - [ ] `isort .` (organize imports)
  - [ ] `flake8 .` (check for violations)
  - [ ] `pytest tests/` (run tests)

### Git Workflow
- [ ] Stage changes: `git add .`
- [ ] Commit with descriptive message: `git commit -m "feat: add new feature"`
- [ ] Push to remote: `git push origin feature/your-feature`
- [ ] Create merge request/pull request

## Testing Setup

### Unit Tests
- [ ] Navigate to tests directory: `cd tests/python`
- [ ] Install test dependencies: `pip install -r requirements.txt`
- [ ] Run unit tests: `pytest unit/ -v`
- [ ] Verify all tests pass

### Integration Tests
- [ ] Configure test AWS credentials (separate from production)
- [ ] Run integration tests: `pytest integration/ -v`
- [ ] Note: Some tests may require specific AWS resources

### Frontend Tests (if applicable)
- [ ] Navigate to frontend: `cd frontend`
- [ ] Run tests: `npm test`
- [ ] Run E2E tests: `npm run test:e2e` (if configured)

## Deployment Understanding

### CloudFormation Templates
- [ ] Review template structure in `cfn/` directory
- [ ] Understand master template and nested stacks
- [ ] Validate templates: `make validate`
- [ ] Lint templates: `make lint`

### Lambda Functions
- [ ] Review Lambda function structure in `lambda/` directory
- [ ] Understand function dependencies and imports
- [ ] Test local Lambda execution (if configured)

### Deployment Process
- [ ] Review deployment script: `scripts/sync-to-deployment-bucket.sh`
- [ ] Understand S3 deployment bucket structure
- [ ] Review CI/CD pipeline in `.gitlab-ci.yml`

## Documentation Review

### Project Documentation
- [ ] Read [README.md](../../README.md) for project overview
- [ ] Review [Architecture Documentation](../architecture/)
- [ ] Understand [API Reference](../guides/API_REFERENCE_GUIDE.md)
- [ ] Read [Development Workflow Guide](../guides/DEVELOPMENT_WORKFLOW_GUIDE.md)

### Coding Standards
- [ ] Review [Python Standards Complete](../../PYTHON_STANDARDS_COMPLETE.md)
- [ ] Understand baseline violations concept
- [ ] Review quality reporting system
- [ ] Understand pre-commit hook limitations

## Verification Tests

### Code Quality Verification
- [ ] Create test Python file with intentional PEP 8 violations
- [ ] Verify IDE shows violations immediately
- [ ] Run Black to fix formatting
- [ ] Run Flake8 to check remaining violations
- [ ] Run isort to organize imports
- [ ] Delete test file

### Development Workflow Verification
- [ ] Create small feature branch
- [ ] Make minor code change
- [ ] Run full quality check pipeline
- [ ] Commit and push changes
- [ ] Verify CI/CD pipeline runs (if configured)

### Lambda Function Verification
- [ ] Open `lambda/index.py` in IDE
- [ ] Verify syntax highlighting works
- [ ] Verify code completion works for AWS SDK
- [ ] Test debug configuration (if possible)

## Team Integration

### Communication Channels
- [ ] Join relevant Slack channels or communication platforms
- [ ] Introduce yourself to team members
- [ ] Schedule onboarding meeting with team lead

### Code Review Process
- [ ] Understand team's code review process
- [ ] Learn about merge request/pull request requirements
- [ ] Understand quality gates and approval process

### Development Practices
- [ ] Learn team's branching strategy
- [ ] Understand commit message conventions
- [ ] Review team's definition of done

## Troubleshooting Common Issues

### Python Environment Issues
- [ ] **Virtual environment not activating**: Check path and shell
- [ ] **Package installation fails**: Upgrade pip, check network/proxy
- [ ] **Import errors**: Verify PYTHONPATH includes lambda and scripts

### IDE Issues
- [ ] **Extensions not working**: Restart IDE, check extension logs
- [ ] **Formatting not working**: Verify tool paths and virtual environment
- [ ] **Linting not showing**: Check tool configuration and file associations

### AWS Issues
- [ ] **Credentials not working**: Run `aws sts get-caller-identity`
- [ ] **Permission errors**: Check IAM policies and roles
- [ ] **Region issues**: Verify AWS_DEFAULT_REGION environment variable

### Git Issues
- [ ] **Pre-commit hooks failing**: Note corporate limitation, use manual checks
- [ ] **Large file issues**: Check .gitignore, avoid committing build artifacts
- [ ] **Merge conflicts**: Learn team's conflict resolution process

## Success Criteria

You've successfully completed onboarding when:

- [ ] **Development Environment**: All tools installed and configured
- [ ] **Code Quality**: Can run all quality checks without errors
- [ ] **IDE Integration**: Automatic formatting and linting work
- [ ] **Testing**: Can run and understand test suite
- [ ] **Documentation**: Familiar with project structure and standards
- [ ] **Workflow**: Can create feature branch, make changes, and submit for review
- [ ] **Team Integration**: Connected with team and understand processes

## Next Steps After Onboarding

1. **First Task Assignment**: Work with team lead to get first development task
2. **Code Review Participation**: Start reviewing others' code to learn patterns
3. **Documentation Contribution**: Improve documentation based on onboarding experience
4. **Tool Mastery**: Deepen knowledge of AWS services and development tools
5. **Process Improvement**: Suggest improvements to onboarding process

## Getting Help

### Documentation Resources
- [Troubleshooting Guide](../guides/TROUBLESHOOTING_GUIDE.md)
- [Development Workflow Guide](../guides/DEVELOPMENT_WORKFLOW_GUIDE.md)
- [API Reference Guide](../guides/API_REFERENCE_GUIDE.md)

### Team Contacts
- **Team Lead**: [Contact Information]
- **DevOps Engineer**: [Contact Information]
- **Senior Developer**: [Contact Information]

### External Resources
- [AWS DRS Documentation](https://docs.aws.amazon.com/drs/)
- [Python PEP 8 Style Guide](https://pep8.org/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [Flake8 Documentation](https://flake8.pycqa.org/)

---

**Estimated Completion Time**: 2-4 hours for experienced developers, 4-8 hours for new team members.

**Last Updated**: January 2026

**Feedback**: Please update this checklist based on your onboarding experience to help future team members.