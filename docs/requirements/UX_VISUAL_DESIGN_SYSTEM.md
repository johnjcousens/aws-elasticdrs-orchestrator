# Visual Design System

## AWS DRS Orchestration System

**Version**: 2.2  
**Status**: Production Ready

---

## Branding & Logo

**Application Title**: Elastic Disaster Recovery Orchestrator

**AWS Logo**:
- URL: `https://a0.awsstatic.com/libra-css/images/logos/aws_smile-header-desktop-en-white_59x35.png`
- Alt text: "AWS"
- Usage: Top navigation and login page

---

## Typography

**Font Family**: `"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif`

| Element | Size | Weight | Usage |
|---------|------|--------|-------|
| Page Title (h1) | 24px | 700 | Main page headers |
| Section Header | 18px | 600 | Container headers |
| Body Text | 14px | 400 | Default text |
| Secondary Text | 12px | 400 | Labels, metadata |
| Tertiary Text | 11px | 400 | IDs, timestamps |

---

## Color Palette

### Primary Colors
| Name | Hex | Usage |
|------|-----|-------|
| AWS Orange | #ec7211 | Primary buttons, CTAs |
| AWS Dark Blue | #232f3e | Login background, headers |
| AWS Navy | #16191f | Primary text |
| White | #ffffff | Card backgrounds |

### Status Colors
| Status | Hex | CloudScape Type | Usage |
|--------|-----|-----------------|-------|
| Success | #037f0c | success | Completed, healthy, validated |
| Active | #0972d3 | in-progress | Running, active, syncing |
| Warning | #d97706 | warning | Paused, limited, pending validation |
| Error | #d13212 | error | Failed, stalled, unauthorized |
| Neutral | #5f6b7a | stopped | Cancelled, pending, disabled |
| Security | #16191f | info | Security validation, audit events |

### UI Colors
| Name | Hex | Usage |
|------|-----|-------|
| Border Light | #e9ebed | Dividers, table borders |
| Background Subtle | #fafafa | Table headers, hover |
| Background Disabled | #f2f3f3 | Disabled elements |

---

## Spacing System

Based on CloudScape design tokens:

| Size | Value | Usage |
|------|-------|-------|
| xs | 8px | Form field gaps, small padding |
| s | 12px | List item padding |
| m | 16px | Container padding, standard gaps |
| l | 24px | Section spacing |
| xl | 32px | Page section margins |

---

## Icons

**CloudScape Icons Used**:
- `notification`, `settings`, `user-profile` - Navigation
- `status-positive`, `status-negative`, `status-warning`, `status-info` - Status indicators
- `refresh`, `add-plus`, `remove`, `edit` - Actions
- `search`, `filter`, `copy` - Utilities
- `security`, `lock-private`, `unlock` - Security and authentication
- `calendar`, `clock`, `schedule` - EventBridge scheduling

**Custom Status Icons** (Wave Progress):
- Job Started: ▶ (#0972d3)
- Job Completed: ✓ (#037f0c)
- Job Failed: ✗ (#d13212)
- Security Validated: 🔒 (#16191f)
- Tag Sync Active: 🔄 (#0972d3)

---

## Layout Dimensions

| Element | Value |
|---------|-------|
| Side Navigation Width | 280px |
| Login Card Max Width | 400px |
| Top Navigation Height | 48px (CloudScape default) |

---

## Implementation

All colors and spacing use CloudScape design tokens. Custom CSS is minimal - CloudScape handles 99% of styling.

**CSS Variables**:
```css
:root {
  --aws-orange: #ec7211;
  --aws-dark-blue: #232f3e;
  --aws-navy: #16191f;
}
```

**Usage in Components**:
```typescript
// Use CloudScape components with standard props
<Button variant="primary">Primary Action</Button>
<StatusIndicator type="success">Completed</StatusIndicator>
<Badge color="green">Active</Badge>
```