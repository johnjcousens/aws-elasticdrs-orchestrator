# HRP DRS Agent Deployment - Quick Reference

## Deployment Strategy

- **01/02 instances** → Same-account (160885257264 → 160885257264)
- **03/04 instances** → Cross-account (160885257264 → 891376951562)

## Quick Commands

### Deploy Everything
```bash
./scripts/deploy-hrp-instances.sh all
```

### Deploy by Strategy
```bash
# Same-account (01/02)
./scripts/deploy-hrp-instances.sh all-01-02

# Cross-account (03/04)
./scripts/deploy-hrp-instances.sh all-03-04
```

### Deploy by Tier
```bash
# Web servers
./scripts/deploy-hrp-instances.sh web-01-02  # Same-account
./scripts/deploy-hrp-instances.sh web-03-04  # Cross-account

# App servers
./scripts/deploy-hrp-instances.sh app-01-02  # Same-account
./scripts/deploy-hrp-instances.sh app-03-04  # Cross-account

# Database servers
./scripts/deploy-hrp-instances.sh db-01-02   # Same-account
./scripts/deploy-hrp-instances.sh db-03-04   # Cross-account
```

## Instance IDs

### 03/04 Instances (Cross-Account) ✅ Ready
| Tier | Instance ID |
|------|-------------|
| Web03 | i-00c5c7b3cf6d8abeb |
| Web04 | i-04d81abd203126050 |
| App03 | i-0b5fcf61e94e9f599 |
| App04 | i-0b40c1c713cfdeac8 |
| DB03 | i-0d780c0fa44ba72e9 |
| DB04 | i-0117a71b9b09d45f7 |

### 01/02 Instances (Same-Account) ⚠️ TODO
Update `scripts/deploy-hrp-instances.sh` with actual instance IDs:
- WEB_01_02
- APP_01_02
- DB_01_02

## Verification

### Check Same-Account (01/02)
```bash
# In source account (160885257264)
aws drs describe-source-servers --region us-east-1
```

### Check Cross-Account (03/04)
```bash
# In staging account (891376951562)
aws drs describe-source-servers --region us-east-1
```

## Prerequisites Checklist

### Same-Account (01/02)
- [ ] DRS initialized in source account (160885257264)
- [ ] Instance profile attached to 01/02 instances
- [ ] SSM Agent running

### Cross-Account (03/04)
- [ ] DRS initialized in staging account (891376951562)
- [ ] Source account added as "Trusted Account" in staging
- [ ] "Failback and in-AWS right-sizing roles" enabled
- [ ] Instance profile attached to 03/04 instances
- [ ] SSM Agent running

## Full Documentation

- [HRP Deployment Strategy](../docs/guides/HRP_DRS_DEPLOYMENT_STRATEGY.md)
- [DRS Agent Deployment README](README-DRS-AGENT-DEPLOYMENT.md)
- [Cross-Account Setup Guide](../DRS_CROSS_ACCOUNT_SETUP.md)
