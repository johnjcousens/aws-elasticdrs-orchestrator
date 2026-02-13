#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { DROrchestrationStack } from '../lib/dr-orchestration-stack';

/**
 * AWS CDK App for DR Orchestration Platform
 * 
 * This example demonstrates deploying the DR Orchestration Platform in headless mode
 * (without API Gateway, Cognito, or frontend) using AWS CDK.
 * 
 * The stack creates:
 * - Lambda functions for query, execution, and data management
 * - DynamoDB tables for protection groups, recovery plans, and executions
 * - Step Functions state machine for wave-based orchestration
 * - EventBridge rules for scheduled operations
 * - IAM roles with proper permissions for direct Lambda invocation
 * 
 * Usage:
 *   npm install
 *   npm run build
 *   cdk deploy
 * 
 * For more information, see README.md
 */

const app = new cdk.App();

// Get configuration from CDK context or environment variables
const environment = app.node.tryGetContext('environment') || process.env.ENVIRONMENT || 'dev';
const projectName = app.node.tryGetContext('projectName') || process.env.PROJECT_NAME || 'hrp-drs-tech-adapter';
const adminEmail = app.node.tryGetContext('adminEmail') || process.env.ADMIN_EMAIL || 'admin@example.com';

// Create the DR Orchestration stack
new DROrchestrationStack(app, `${projectName}-${environment}`, {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  description: `DR Orchestration Platform - ${environment} environment (headless mode)`,
  
  // Stack configuration
  projectName,
  environment,
  adminEmail,
  
  // Deployment mode: headless (no API Gateway, Cognito, or frontend)
  deployApiGateway: false,
  
  // Optional: Enable tag synchronization
  enableTagSync: true,
  
  // Optional: Enable email notifications
  enableNotifications: false,
  
  // Tags for resource organization
  tags: {
    Project: 'DROrchestration',
    Environment: environment,
    ManagedBy: 'CDK',
    DeploymentMode: 'Headless',
  },
});

app.synth();
