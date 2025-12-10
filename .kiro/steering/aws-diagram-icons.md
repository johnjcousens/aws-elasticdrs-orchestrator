# AWS Diagram Icon Standards

## AWS 2025 (AWS4) Icon Set

When creating AWS architecture diagrams using draw.io or the aws-diagram-mcp, always use the AWS4 2025 icon format.

### Icon Style Format

All AWS service icons must use this style pattern:
```
sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=<SERVICE_COLOR>;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.<service_name>;
```

### Official AWS Service Colors (2025)

| Category | Color | Services |
|----------|-------|----------|
| Compute | #ED7100 | lambda, ec2, ecs, eks, fargate, batch |
| Storage | #7AA116 | s3, efs, fsx, elastic_block_store, elastic_disaster_recovery |
| Database | #C925D1 | dynamodb, rds, aurora, redshift, elasticache |
| Networking | #8C4FFF | vpc, cloudfront, route53, api_gateway_endpoint, elastic_load_balancing |
| App Integration | #E7157B | api_gateway, step_functions, eventbridge, sns, sqs, cloudwatch, cloudtrail, cloudformation, systems_manager |
| Security | #DD344C | cognito, iam, waf, shield, secrets_manager, kms |

### Common Service Icon Names

| Service | resIcon Value |
|---------|---------------|
| Lambda | mxgraph.aws4.lambda |
| S3 | mxgraph.aws4.s3 |
| DynamoDB | mxgraph.aws4.dynamodb |
| API Gateway | mxgraph.aws4.api_gateway |
| CloudFront | mxgraph.aws4.cloudfront |
| Cognito | mxgraph.aws4.cognito |
| Step Functions | mxgraph.aws4.step_functions |
| EventBridge | mxgraph.aws4.eventbridge |
| CloudWatch | mxgraph.aws4.cloudwatch |
| CloudTrail | mxgraph.aws4.cloudtrail |
| CloudFormation | mxgraph.aws4.cloudformation |
| IAM | mxgraph.aws4.iam |
| WAF | mxgraph.aws4.waf |
| SNS | mxgraph.aws4.sns |
| SQS | mxgraph.aws4.sqs |
| EC2 | mxgraph.aws4.ec2 |
| ECS | mxgraph.aws4.ecs |
| EKS | mxgraph.aws4.eks |
| RDS | mxgraph.aws4.rds |
| Aurora | mxgraph.aws4.aurora |
| ElastiCache | mxgraph.aws4.elasticache |
| VPC | mxgraph.aws4.vpc |
| Route 53 | mxgraph.aws4.route_53 |
| Systems Manager | mxgraph.aws4.systems_manager |
| Secrets Manager | mxgraph.aws4.secrets_manager |
| KMS | mxgraph.aws4.kms |
| EBS | mxgraph.aws4.elastic_block_store |
| DRS | mxgraph.aws4.elastic_disaster_recovery |

### Example Icon Cell

```xml
<mxCell id="lambda-function" value="My Lambda" style="sketch=0;outlineConnect=0;fontColor=#232F3E;fillColor=#ED7100;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=11;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.lambda;" parent="1" vertex="1">
  <mxGeometry x="100" y="100" width="78" height="78" as="geometry" />
</mxCell>
```

### Do NOT Use

- Old rounded rectangle boxes with solid colors
- Generic shapes without AWS4 icons
- Outdated AWS3 icon format
- Custom non-standard colors
