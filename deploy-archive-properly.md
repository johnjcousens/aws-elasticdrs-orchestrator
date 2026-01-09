# Deploy Archive Test Stack Properly

## The Problem
I've been deploying the CURRENT (broken) architecture to the archive test stack instead of the WORKING archive architecture.

## What Should Happen
- Archive test stack should use: `archive/commit-9546118-uncorrupted/cfn/master-template.yaml`
- Archive test stack should use: Archive Lambda code (working orchestration)
- Archive test stack should use: Simple 5-stack architecture that actually worked

## Current Wrong Approach
- Using current `cfn/master-template.yaml` (12 stacks, broken)
- Using current Lambda code (broken orchestration)
- Deploying complex architecture that doesn't work

## Correct Approach Needed
1. Copy archive CFN templates to deployment bucket under `archive/` prefix
2. Copy archive Lambda code (properly packaged) to deployment bucket under `archive/` prefix  
3. Modify GitHub Actions to use archive templates for archive test stack
4. Deploy the WORKING 5-stack architecture

This way we can actually compare working vs broken implementations.