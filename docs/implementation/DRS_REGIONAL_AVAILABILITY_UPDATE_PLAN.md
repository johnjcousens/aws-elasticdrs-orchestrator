# DRS Regional Availability Update - Implementation Plan

## Executive Summary

Update the AWS DRS regional availability information across the UI and documentation to reflect the current 28 commercial regions + 2 GovCloud regions as verified from the official AWS DRS endpoints documentation.

**Reference**: [AWS DRS Endpoints and Quotas](https://docs.aws.amazon.com/general/latest/gr/drs.html)
**Last Verified**: December 10, 2025

## Current State vs Required State

### Current Documentation (Outdated)

The README.md currently shows only 14 regions:
- Americas: 5 regions
- Europe: 6 regions  
- Asia Pacific: 3 regions

### Verified AWS DRS Availability (28 Commercial + 2 GovCloud)

| Region Group | Count | Regions |
|--------------|-------|---------|
| **Americas** | 6 | us-east-1, us-east-2, us-west-1, us-west-2, ca-central-1, sa-east-1 |
| **Europe** | 8 | eu-west-1, eu-west-2, eu-west-3, eu-central-1, eu-central-2, eu-north-1, eu-south-1, eu-south-2 |
| **Asia Pacific** | 10 | ap-northeast-1, ap-northeast-2, ap-northeast-3, ap-southeast-1, ap-southeast-2, ap-southeast-3, ap-southeast-4, ap-south-1, ap-south-2, ap-east-1 |
| **Middle East & Africa** | 4 | me-south-1, me-central-1, af-south-1, il-central-1 |
| **GovCloud** | 2 | us-gov-east-1, us-gov-west-1 |

**Note**: Canada West (ca-west-1) is NOT in AWS DRS endpoints.

## Files to Update

### 1. README.md

**Location**: AWS DRS Regional Availability section (~line 68)

**Current**:
```markdown
## AWS DRS Regional Availability

**Americas (5 regions)**: US East (N. Virginia, Ohio), US West (Oregon, N. California), Canada (Central)  
**Europe (6 regions)**: Ireland, London, Frankfurt, Paris, Stockholm, Milan  
**Asia Pacific (3 regions)**: Tokyo, Sydney, Singapore
```

**Updated**:
```markdown
## AWS DRS Regional Availability

The solution orchestrates disaster recovery in all **30 AWS regions** where Elastic Disaster Recovery (DRS) is available:

| Region Group | Count | Regions |
|--------------|-------|---------|
| **Americas** | 6 | US East (N. Virginia, Ohio), US West (Oregon, N. California), Canada (Central), South America (São Paulo) |
| **Europe** | 8 | Ireland, London, Frankfurt, Paris, Stockholm, Milan, Spain, Zurich |
| **Asia Pacific** | 10 | Tokyo, Seoul, Osaka, Singapore, Sydney, Mumbai, Hyderabad, Jakarta, Melbourne, Hong Kong |
| **Middle East & Africa** | 4 | Bahrain, UAE, Cape Town, Tel Aviv |
| **GovCloud** | 2 | US-East, US-West |

*Regional availability determined by AWS DRS service. As AWS expands DRS, the solution automatically supports new regions.*
```

### 2. Frontend Region Selector

**File**: `frontend/src/components/RegionSelector.tsx`

Update the `DRS_REGIONS` constant with all 30 regions.

### 3. Research Document

**File**: `docs/research/AWS_DRS_SERVICE_LIMITS_AND_CAPABILITIES_RESEARCH.md`

Already updated with correct regional information.

## Implementation

### Step 1: Update Frontend Region Data

**File**: `frontend/src/components/RegionSelector.tsx` or `frontend/src/constants/regions.ts`

```typescript
export const DRS_SUPPORTED_REGIONS = [
  // Americas (6)
  { code: 'us-east-1', name: 'US East (N. Virginia)', group: 'Americas' },
  { code: 'us-east-2', name: 'US East (Ohio)', group: 'Americas' },
  { code: 'us-west-1', name: 'US West (N. California)', group: 'Americas' },
  { code: 'us-west-2', name: 'US West (Oregon)', group: 'Americas' },
  { code: 'ca-central-1', name: 'Canada (Central)', group: 'Americas' },
  { code: 'sa-east-1', name: 'South America (São Paulo)', group: 'Americas' },
  
  // Europe (8)
  { code: 'eu-west-1', name: 'Europe (Ireland)', group: 'Europe' },
  { code: 'eu-west-2', name: 'Europe (London)', group: 'Europe' },
  { code: 'eu-west-3', name: 'Europe (Paris)', group: 'Europe' },
  { code: 'eu-central-1', name: 'Europe (Frankfurt)', group: 'Europe' },
  { code: 'eu-central-2', name: 'Europe (Zurich)', group: 'Europe' },
  { code: 'eu-north-1', name: 'Europe (Stockholm)', group: 'Europe' },
  { code: 'eu-south-1', name: 'Europe (Milan)', group: 'Europe' },
  { code: 'eu-south-2', name: 'Europe (Spain)', group: 'Europe' },
  
  // Asia Pacific (10)
  { code: 'ap-northeast-1', name: 'Asia Pacific (Tokyo)', group: 'Asia Pacific' },
  { code: 'ap-northeast-2', name: 'Asia Pacific (Seoul)', group: 'Asia Pacific' },
  { code: 'ap-northeast-3', name: 'Asia Pacific (Osaka)', group: 'Asia Pacific' },
  { code: 'ap-southeast-1', name: 'Asia Pacific (Singapore)', group: 'Asia Pacific' },
  { code: 'ap-southeast-2', name: 'Asia Pacific (Sydney)', group: 'Asia Pacific' },
  { code: 'ap-southeast-3', name: 'Asia Pacific (Jakarta)', group: 'Asia Pacific' },
  { code: 'ap-southeast-4', name: 'Asia Pacific (Melbourne)', group: 'Asia Pacific' },
  { code: 'ap-south-1', name: 'Asia Pacific (Mumbai)', group: 'Asia Pacific' },
  { code: 'ap-south-2', name: 'Asia Pacific (Hyderabad)', group: 'Asia Pacific' },
  { code: 'ap-east-1', name: 'Asia Pacific (Hong Kong)', group: 'Asia Pacific' },
  
  // Middle East & Africa (4)
  { code: 'me-south-1', name: 'Middle East (Bahrain)', group: 'Middle East & Africa' },
  { code: 'me-central-1', name: 'Middle East (UAE)', group: 'Middle East & Africa' },
  { code: 'af-south-1', name: 'Africa (Cape Town)', group: 'Middle East & Africa' },
  { code: 'il-central-1', name: 'Israel (Tel Aviv)', group: 'Middle East & Africa' },
  
  // GovCloud (2) - Optional, may require separate handling
  // { code: 'us-gov-east-1', name: 'AWS GovCloud (US-East)', group: 'GovCloud' },
  // { code: 'us-gov-west-1', name: 'AWS GovCloud (US-West)', group: 'GovCloud' },
];

export const DRS_REGION_COUNT = {
  commercial: 28,
  govcloud: 2,
  total: 30
};
```

### Step 2: Update README.md

Replace the AWS DRS Regional Availability section with the updated table format.

### Step 3: Update Steering Rules and Requirements Documentation

**Files**:
- `.kiro/steering/product.md` - Update regional availability section
- `docs/requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md` - Update regional availability
- `docs/requirements/SOFTWARE_REQUIREMENTS_SPECIFICATION.md` - Update regional constraints

Update all documentation to reflect the correct 30 AWS DRS regions.

## Validation Checklist

- [ ] README.md updated with 30 regions in table format
- [ ] Frontend RegionSelector has all 28 commercial regions
- [ ] Research document verified (already correct)
- [ ] `.kiro/steering/product.md` updated
- [ ] `docs/requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md` updated
- [ ] `docs/requirements/SOFTWARE_REQUIREMENTS_SPECIFICATION.md` updated
- [ ] No references to ca-west-1 (not supported)
- [ ] GovCloud regions documented but may be excluded from commercial UI

## Notes

1. **GovCloud Handling**: GovCloud regions (us-gov-east-1, us-gov-west-1) require separate AWS partitions and may need special handling in the UI. Consider:
   - Excluding from standard region selector
   - Adding a separate "GovCloud" toggle if needed
   - Documenting GovCloud support separately

2. **Dynamic Region Discovery**: Consider future enhancement to dynamically fetch DRS-supported regions from AWS API rather than hardcoding.

3. **Region Opt-In**: Some regions (ap-east-1, me-south-1, af-south-1, eu-south-2, ap-southeast-3, ap-southeast-4, eu-central-2, me-central-1, il-central-1, ap-south-2) require opt-in. The UI should handle cases where a region is not enabled in the user's account.
