# Configuration Directory

This directory contains environment-specific configuration files for the AWS DRS Orchestration solution.

## Environment Files

### `environments/`

Environment-specific configuration files used for deployment and frontend builds:

| File | Purpose | Usage |
|------|---------|-------|
| `.env.dev` | Development environment | Complete dev stack configuration with actual values |
| `.env.prod` | Production environment | Production stack configuration with actual values |
| `.env.production` | Production template | Empty template for production deployment |
| `.env.test.template` | Test template | Template for creating test environment config |

### Usage Instructions

#### For New Environment Setup:
1. Copy the appropriate template:
   ```bash
   cp config/environments/.env.test.template config/environments/.env.test
   ```

2. Get values from CloudFormation stack outputs:
   ```bash
   aws cloudformation describe-stacks \
     --stack-name aws-drs-orchestrator-test \
     --region us-east-1 \
     --query 'Stacks[0].Outputs'
   ```

3. Populate the environment file with actual values

4. Use in deployment:
   ```bash
   ./scripts/sync-to-deployment-bucket.sh --build-frontend --deploy-cfn
   ```

#### For Frontend Development:
The frontend build process uses these files to generate `aws-config.json` with the correct API endpoints and Cognito configuration.

#### Security Note:
- Environment files with actual values (`.env.dev`, `.env.prod`) contain sensitive information
- Template files (`.env.test.template`, `.env.production`) are safe to commit
- Never commit files with actual AWS resource IDs or endpoints to public repositories

## File Structure

```
config/
├── README.md                    # This file
└── environments/
    ├── .env.dev                 # Development configuration (actual values)
    ├── .env.prod                # Production configuration (actual values)  
    ├── .env.production          # Production template (empty values)
    └── .env.test.template       # Test template (empty values)
```