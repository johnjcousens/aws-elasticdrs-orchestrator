---
inclusion: fileMatch
fileMatchPattern: 'frontend/**/*.{tsx,ts,css}'
---

# CloudScape Design Practices for AWS DRS Orchestration

## Purpose

This document establishes CloudScape Design System best practices for the AWS DRS Orchestration frontend application, ensuring compliance with official AWS Management Console design standards and maintaining visual consistency across AWS services.

## Official AWS Design Standards

Based on AWS's official visual update announcement and CloudScape documentation:

### Core Design Principles

1. **Color Usage**
   - Blue is the primary interactive color for buttons, links, tokens, and interactive states
   - Colors reinforce brand and user actions while maintaining strong contrast
   - Color should never be the only visual means of conveying information

2. **Typography**
   - Revised typography scale with improved heading treatment
   - Labels and keys should be prominent for easier scanning
   - Stronger visual hierarchy helps locate and understand data

3. **Visual Hierarchy**
   - Reduced visual complexity with thinner strokes on containers
   - Unified border styles across components
   - Strategic use of shadows only for interactive/transient elements

4. **Information Density**
   - Optimized spacing with related data displayed closer together
   - Minimized space within containers
   - Centered wider layouts for modern screen sizes

5. **Consistency**
   - Distinctive and consistent interface using CloudScape design tokens
   - Unified experience across all AWS services

## Design Token Usage

### What Are Design Tokens?

Design tokens are named variables representing design decisions (colors, spacing, typography). They provide:
- Automatic theme adaptation (light/dark mode)
- Consistent visual language
- Maintainable styling
- AWS brand compliance

### Token Categories

CloudScape provides tokens for:
- **Colors**: Text, background, border, status
- **Spacing**: xxxs to xxl scale
- **Typography**: Font sizes, weights, line heights
- **Shadows and borders**: Depth and separation
- **Motion**: Animation durations

### Token Naming Convention

Tokens follow semantic naming:
- `color-text-body-default` - Default body text color
- `color-background-button-primary-default` - Primary button background
- `space-scaled-m` - Medium spacing (scales with density)
- `font-size-body-m` - Medium body font size

## CSS Architecture

### NEVER Use Inline Styles

❌ **WRONG:**
```typescript
<div style={{ color: '#5f6b7a', fontSize: '14px', marginBottom: '8px' }}>
  Label
</div>
```

✅ **CORRECT:**
```typescript
// Component.module.css
.label {
  color: var(--awsui-color-text-body-secondary);
  font-size: var(--awsui-font-size-body-m);
  margin-bottom: var(--awsui-space-scaled-xs);
}

// Component.tsx
import styles from './Component.module.css';

<div className={styles.label}>Label</div>
```

### CSS Module Structure

**File Organization:**
```
components/
├── MyComponent.tsx
├── MyComponent.module.css
└── __tests__/
    └── MyComponent.test.tsx
```

**Naming Convention:**
- Use camelCase for CSS class names: `.myClassName`
- Use camelCase for CSS custom properties: `--myCustomProperty`
- Match component name: `MyComponent.module.css`

**Example CSS Module:**
```css
/* MyComponent.module.css */

.container {
  background-color: var(--awsui-color-background-container-content);
  border: 1px solid var(--awsui-color-border-container-top);
  border-radius: var(--awsui-border-radius-container);
  padding: var(--awsui-space-scaled-m);
}

.header {
  color: var(--awsui-color-text-heading-default);
  font-size: var(--awsui-font-size-heading-m);
  font-weight: var(--awsui-font-weight-heading);
  margin-bottom: var(--awsui-space-scaled-s);
}

.label {
  color: var(--awsui-color-text-label);
  font-size: var(--awsui-font-size-body-s);
  font-weight: var(--awsui-font-weight-bold);
}

.value {
  color: var(--awsui-color-text-body-default);
  font-size: var(--awsui-font-size-body-m);
}
```

**TypeScript Import:**
```typescript
import styles from './MyComponent.module.css';

export const MyComponent: React.FC = () => {
  return (
    <div className={styles.container}>
      <h2 className={styles.header}>Title</h2>
      <div className={styles.label}>Label</div>
      <div className={styles.value}>Value</div>
    </div>
  );
};
```

## Common Design Token Patterns

### Colors

**Text Colors:**
```css
.primaryText {
  color: var(--awsui-color-text-body-default);
}

.secondaryText {
  color: var(--awsui-color-text-body-secondary);
}

.labelText {
  color: var(--awsui-color-text-label);
}

.headingText {
  color: var(--awsui-color-text-heading-default);
}

.linkText {
  color: var(--awsui-color-text-link-default);
}
```

**Background Colors:**
```css
.containerBackground {
  background-color: var(--awsui-color-background-container-content);
}

.layoutBackground {
  background-color: var(--awsui-color-background-layout-main);
}

.buttonPrimaryBackground {
  background-color: var(--awsui-color-background-button-primary-default);
}
```

**Status Colors:**
```css
.successText {
  color: var(--awsui-color-text-status-success);
}

.errorText {
  color: var(--awsui-color-text-status-error);
}

.warningText {
  color: var(--awsui-color-text-status-warning);
}

.infoText {
  color: var(--awsui-color-text-status-info);
}
```

**Border Colors:**
```css
.containerBorder {
  border: 1px solid var(--awsui-color-border-container-top);
}

.dividerBorder {
  border-bottom: 1px solid var(--awsui-color-border-divider-default);
}

.inputBorder {
  border: 1px solid var(--awsui-color-border-input-default);
}
```

### Spacing

**CloudScape Spacing Scale:**
- `xxxs`: 2px
- `xxs`: 4px
- `xs`: 8px
- `s`: 12px
- `m`: 16px
- `l`: 20px
- `xl`: 24px
- `xxl`: 32px

**Usage:**
```css
.tightSpacing {
  padding: var(--awsui-space-scaled-xs);
  gap: var(--awsui-space-scaled-xxs);
}

.normalSpacing {
  padding: var(--awsui-space-scaled-m);
  gap: var(--awsui-space-scaled-s);
}

.generousSpacing {
  padding: var(--awsui-space-scaled-l);
  gap: var(--awsui-space-scaled-m);
}
```

### Typography

**Font Sizes:**
```css
.smallText {
  font-size: var(--awsui-font-size-body-s);
}

.normalText {
  font-size: var(--awsui-font-size-body-m);
}

.headingSmall {
  font-size: var(--awsui-font-size-heading-s);
}

.headingMedium {
  font-size: var(--awsui-font-size-heading-m);
}

.headingLarge {
  font-size: var(--awsui-font-size-heading-l);
}
```

**Font Weights:**
```css
.normalWeight {
  font-weight: var(--awsui-font-weight-normal);
}

.boldWeight {
  font-weight: var(--awsui-font-weight-bold);
}

.headingWeight {
  font-weight: var(--awsui-font-weight-heading);
}
```

## Z-Index Layering System

**Centralized Z-Index Scale:**

Create `frontend/src/styles/z-index.css`:
```css
:root {
  --z-index-base: 0;
  --z-index-dropdown: 1000;
  --z-index-modal-overlay: 1999;
  --z-index-modal: 2000;
  --z-index-tooltip: 3000;
  --z-index-notification: 4000;
}
```

**Usage:**
```css
.dropdown {
  z-index: var(--z-index-dropdown);
}

.modalOverlay {
  z-index: var(--z-index-modal-overlay);
}

.modal {
  z-index: var(--z-index-modal);
}
```

**Rules:**
- NEVER use hardcoded z-index values
- ALWAYS use the centralized z-index scale
- Document any new z-index layers

## AWS Console Design Compliance

### Interactive Elements

**Primary Actions:**
```typescript
// Use CloudScape Button component
<Button variant="primary">Create</Button>
```

**Secondary Actions:**
```typescript
<Button>Cancel</Button>
```

**Links:**
```typescript
<Link href="/path">View details</Link>
```

### Status Indicators

**ALWAYS pair color with iconography or text:**

❌ **WRONG:**
```typescript
<div style={{ color: '#037f0c' }}>Success</div>
```

✅ **CORRECT:**
```typescript
<StatusIndicator type="success">Completed</StatusIndicator>
```

### Containers and Cards

**Use thin borders, not shadows:**

❌ **WRONG:**
```css
.card {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
```

✅ **CORRECT:**
```css
.card {
  border: 1px solid var(--awsui-color-border-container-top);
  border-radius: var(--awsui-border-radius-container);
}
```

**Reserve shadows for interactive elements:**
```css
.dropdown {
  box-shadow: var(--awsui-shadow-dropdown);
}

.modal {
  box-shadow: var(--awsui-shadow-modal);
}
```

## CloudScape Component Styling Rules

### CRITICAL: Do NOT Override CloudScape Components

According to CloudScape documentation, **custom CSS classes on CloudScape components are deprecated** because the internal HTML and CSS structure can change with updates.

❌ **WRONG - DO NOT DO THIS:**
```typescript
// Adding className to CloudScape components is DEPRECATED
<Button className={styles.customButton}>Click</Button>

// Overriding CloudScape internal styles will break on updates
.customButton {
  background-color: red !important; // NEVER DO THIS
}
```

✅ **CORRECT - DO THIS INSTEAD:**
```typescript
// Option 1: Wrap in styled div
<div className={styles.buttonWrapper}>
  <Button variant="primary">Click</Button>
</div>

// Option 2: Use CloudScape's built-in variant props
<Button variant="primary">Click</Button>
<Button variant="normal">Click</Button>
<Button variant="link">Click</Button>
```

## CSS Module File Organization

### Directory Structure
```
frontend/src/
├── styles/
│   ├── z-index.css           # Centralized z-index scale
│   ├── utilities.css         # Shared utility classes
│   └── design-tokens.md      # Token reference
├── components/
│   ├── MyComponent.tsx
│   └── MyComponent.module.css
└── pages/
    ├── Dashboard.tsx
    └── Dashboard.module.css
```

### Utility Classes (styles/utilities.css)
```css
/* Flexbox utilities */
.flexRow { display: flex; flex-direction: row; align-items: center; }
.flexColumn { display: flex; flex-direction: column; }
.flexBetween { display: flex; justify-content: space-between; }

/* Spacing utilities */
.gapXs { gap: var(--awsui-space-scaled-xs); }
.gapS { gap: var(--awsui-space-scaled-s); }
.gapM { gap: var(--awsui-space-scaled-m); }

/* Text utilities */
.textSecondary { color: var(--awsui-color-text-body-secondary); }
.textMuted { 
  color: var(--awsui-color-text-body-secondary);
  font-size: var(--awsui-font-size-body-s);
}
```

## Summary

### Key Principles
1. **Zero inline styles** - Use CSS modules with design tokens
2. **100% CloudScape tokens** - No hardcoded values
3. **Never override CloudScape** - Wrap components, don't modify
4. **Centralized z-index** - Use shared scale
5. **camelCase naming** - Consistent class names
6. **Thin borders** - 1px for containers
7. **Strategic shadows** - Only for interactive elements
8. **AWS Console compliance** - Follow official design standards

### Resources
- CloudScape Design System: https://cloudscape.design/
- Design Tokens: https://cloudscape.design/foundation/visual-foundation/design-tokens/
- AWS Visual Update: https://aws.amazon.com/blogs/aws/new-aws-management-console-visual-refresh/ary">Primary Action</Button>
<Button variant="normal">Secondary Action</Button>
<Button variant="link">Link Action</Button>

// Option 3: Use CloudScape spacing components
<SpaceBetween direction="horizontal" size="xs">
  <Button>Cancel</Button>
  <Button variant="primary">Save</Button>
</SpaceBetween>
```

### CloudScape Component Best Practices

**DO:**
- ✅ Wrap CloudScape components in styled divs for custom layouts
- ✅ Use CloudScape component variant props (e.g., `variant="primary"`)
- ✅ Use CloudScape spacing components (SpaceBetween, Box)
- ✅ Use CloudScape design tokens in custom CSS
- ✅ Style custom wrapper components with CSS modules

**DON'T:**
- ❌ Add className to CloudScape components (deprecated)
- ❌ Override CloudScape component internal styles
- ❌ Use !important to override CloudScape styles
- ❌ Rely on CloudScape internal HTML structure
- ❌ Target CloudScape internal class names

### Example: Styling Around CloudScape Components

```typescript
// MyComponent.module.css
.actionContainer {
  display: flex;
  justify-content: flex-end;
  gap: var(--awsui-space-scaled-xs);
  padding: var(--awsui-space-scaled-m);
  background-color: var(--awsui-color-background-container-content);
  border-top: 1px solid var(--awsui-color-border-divider-default);
}

// MyComponent.tsx
import styles from './MyComponent.module.css';

export const MyComponent: React.FC = () => {
  return (
    <div className={styles.actionContainer}>
      <Button>Cancel</Button>
      <Button variant="primary">Save</Button>
    </div>
  );
};
```

## Bidirectional Text Support (RTL/LTR)

CloudScape components automatically support bidirectional text without any additional implementation effort.

### Key Principles

1. **Inherit Direction**: CloudScape components do not declare a direction of either LTR or RTL. Instead, the direction is inherited from the context in which the components are used.

2. **No Direction-Specific API**: There is no direction-specific API or implementation effort required to enable RTL support.

3. **Use Logical Properties**: When writing custom CSS, prefer logical properties over directional ones:

❌ **WRONG:**
```css
.container {
  margin-left: 16px;
  padding-right: 8px;
  text-align: left;
}
```

✅ **CORRECT:**
```css
.container {
  margin-inline-start: var(--awsui-space-scaled-m);
  padding-inline-end: var(--awsui-space-scaled-xs);
  text-align: start;
}
```

### Logical CSS Properties Reference

| Physical Property | Logical Property |
|------------------|------------------|
| `margin-left` | `margin-inline-start` |
| `margin-right` | `margin-inline-end` |
| `padding-left` | `padding-inline-start` |
| `padding-right` | `padding-inline-end` |
| `border-left` | `border-inline-start` |
| `border-right` | `border-inline-end` |
| `left` | `inset-inline-start` |
| `right` | `inset-inline-end` |
| `text-align: left` | `text-align: start` |
| `text-align: right` | `text-align: end` |

## Dynamic Styling

When dynamic values are required, use CSS custom properties:

❌ **WRONG:**
```typescript
<div style={{ width: `${progress}%` }}>Progress</div>
```

✅ **CORRECT:**
```typescript
// Component.module.css
.progressBar {
  width: var(--progress-width);
  background-color: var(--awsui-color-background-button-primary-default);
}

// Component.tsx
<div 
  className={styles.progressBar}
  style={{ '--progress-width': `${progress}%` } as React.CSSProperties}
>
  Progress
</div>
```

## Migration Checklist

When refactoring a component:

- [ ] Remove all inline `style={{}}` attributes
- [ ] Create corresponding CSS module file
- [ ] Replace hardcoded colors with CloudScape tokens
- [ ] Replace hardcoded spacing with CloudScape tokens
- [ ] Replace hardcoded font sizes with CloudScape tokens
- [ ] Use centralized z-index scale if needed
- [ ] Ensure accessibility (color + icon/text)
- [ ] Test in light and dark mode
- [ ] Verify visual consistency with before state

## Resources

### Official Documentation

- **CloudScape Homepage**: https://cloudscape.design/
- **Foundation**: https://cloudscape.design/foundation/
  - Visual Foundation (colors, typography, spacing, motion)
  - Design Tokens: https://cloudscape.design/foundation/visual-foundation/design-tokens
  - Colors: https://cloudscape.design/foundation/visual-foundation/colors/
- **Components** (60+ components): https://cloudscape.design/components/
  - Layout components (AppLayout, ContentLayout, Grid, Box)
  - Form components (Input, Select, Checkbox, DatePicker)
  - Navigation (SideNavigation, TopNavigation, Tabs, Breadcrumbs)
  - Data display (Table, Cards, StatusIndicator, Badge)
  - Feedback (Modal, Flashbar, Alert, Popover)
  - Charts (Line, Bar, Area, Pie, Mixed)
- **Patterns** (30+ patterns): https://cloudscape.design/patterns/
  - Create/Edit/Delete patterns
  - Table and collection views
  - Dashboard patterns
  - Form validation
  - Empty states and error handling
- **Demos** (20+ demos): https://cloudscape.design/demos/
  - Complete working examples
  - Table views with filtering and pagination
  - Create/edit forms
  - Dashboard layouts
  - Generative AI chat interfaces

### AWS Resources

- **AWS Console Visual Update**: https://aws.amazon.com/blogs/aws/announcing-a-visual-update-to-the-aws-management-console-preview/
- **CloudScape Open Source**: https://www.amazon.design/systems-design/cloudscape-open-source-design-system
- **GitHub Repository**: https://github.com/cloudscape-design/components

### Package Installation

```bash
# Install CloudScape components
npm install @cloudscape-design/components @cloudscape-design/global-styles

# Install design tokens (optional, for custom components)
npm install @cloudscape-design/design-tokens
```

### Design Resources

- **Figma Design Library**: Available for designers to create CloudScape designs
- **Style Dictionary**: For converting design tokens to other formats (iOS, Android)

## Quick Reference

### Common Token Replacements

| Hardcoded Value | CloudScape Token |
|----------------|------------------|
| `#5f6b7a` | `var(--awsui-color-text-body-secondary)` |
| `#16191f` | `var(--awsui-color-text-body-default)` |
| `#0972d3` | `var(--awsui-color-text-link-default)` |
| `#037f0c` | `var(--awsui-color-text-status-success)` |
| `#d13212` | `var(--awsui-color-text-status-error)` |
| `#ffffff` | `var(--awsui-color-background-container-content)` |
| `#f2f3f3` | `var(--awsui-color-background-layout-main)` |
| `8px` | `var(--awsui-space-scaled-xs)` |
| `16px` | `var(--awsui-space-scaled-m)` |
| `14px` | `var(--awsui-font-size-body-m)` |
| `12px` | `var(--awsui-font-size-body-s)` |

### Naming Conventions

- **CSS Classes**: camelCase (`.myClassName`)
- **CSS Custom Properties**: camelCase (`--myCustomProperty`)
- **Component Files**: PascalCase (`MyComponent.tsx`)
- **CSS Module Files**: PascalCase (`MyComponent.module.css`)
- **JavaScript Variables**: camelCase (`myVariable`)
- **API Data**: Transform PascalCase to camelCase at boundary

### CloudScape Component Variants

Common variant props for CloudScape components:

**Button:**
- `variant="primary"` - Primary action (blue)
- `variant="normal"` - Secondary action (default)
- `variant="link"` - Link-style button
- `variant="icon"` - Icon-only button

**Header:**
- `variant="h1"` - Page title
- `variant="h2"` - Section heading
- `variant="h3"` - Subsection heading

**Container:**
- `variant="default"` - Standard container
- `variant="stacked"` - Stacked layout

**StatusIndicator:**
- `type="success"` - Green checkmark
- `type="error"` - Red X
- `type="warning"` - Orange warning
- `type="info"` - Blue info
- `type="pending"` - Gray pending
- `type="in-progress"` - Blue spinner
- `type="loading"` - Loading spinner
