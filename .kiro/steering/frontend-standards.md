---
inclusion: fileMatch
fileMatchPattern: 'frontend/**/*.{tsx,ts,css}'
---

# Frontend & CloudScape Standards

Consolidated frontend standards: CloudScape component patterns, design tokens, CSS architecture, and DRS-specific branding.

## Critical Rules

- ALWAYS use CloudScape components exclusively — no Bootstrap, Tailwind, or custom UI frameworks
- NEVER override CloudScape component styles with className (deprecated) or !important
- NEVER use inline styles — use CSS modules with design tokens
- ALWAYS use CloudScape light mode theme (AWS Console standard)
- ALWAYS follow the `detail` property pattern for CloudScape events

## AWS Branding (DRS Orchestrator)

### Top Navigation
```typescript
<TopNavigation
  identity={{
    href: '/',
    title: 'Elastic Disaster Recovery Orchestrator',
    logo: {
      src: 'https://a0.awsstatic.com/libra-css/images/logos/aws_smile-header-desktop-en-white_59x35.png',
      alt: 'AWS',
    },
  }}
/>
```

### Navigation Items (Maintain Order)
```typescript
const navigationItems = [
  { type: 'link', text: 'Dashboard', href: '/' },
  { type: 'divider' },
  { type: 'link', text: 'Getting Started', href: '/getting-started' },
  { type: 'link', text: 'Protection Groups', href: '/protection-groups' },
  { type: 'link', text: 'Recovery Plans', href: '/recovery-plans' },
  { type: 'link', text: 'History', href: '/executions' },
];
```

### Status Colors
```typescript
const STATUS_COLORS = {
  completed: '#037f0c',    // AWS Green
  in_progress: '#0972d3',  // AWS Blue
  pending: '#5f6b7a',      // AWS Grey
  failed: '#d91515',       // AWS Red
  rolled_back: '#ff9900',  // AWS Orange
  cancelled: '#5f6b7a',
  paused: '#5f6b7a',
};

const getStatusType = (status: string) => {
  switch (status) {
    case 'completed': return 'success';
    case 'failed': return 'error';
    case 'rolled_back': return 'warning';
    case 'cancelled':
    case 'paused': return 'stopped';
    default: return 'in-progress';
  }
};
```

## Layout Structure

### Page Structure (Mandatory)
```typescript
// Protected routes: AppLayout → ContentLayout → Container
<ProtectedRoute>
  <AppLayout
    navigation={<SideNavigation items={navItems} />}
    content={
      <ContentLayout
        header={<Header variant="h1" actions={<Button variant="primary">Create</Button>}>Page Title</Header>}
      >
        <SpaceBetween size="l">
          <Container header={<Header variant="h2">Section</Header>}>
            {/* content */}
          </Container>
        </SpaceBetween>
      </ContentLayout>
    }
    breadcrumbs={<BreadcrumbGroup items={breadcrumbs} />}
    notifications={<Flashbar items={notifications} />}
  />
</ProtectedRoute>

// Login/public pages: NO AppLayout
<Route path="/login" element={<LoginPage />} />
```

## Forms

### FormField Pattern (Always Use)
```typescript
<FormField label="Name" description="Enter a unique name" errorText={errors.name}>
  <Input value={name} onChange={({ detail }) => setName(detail.value)} />
</FormField>

<FormField label="Region">
  <Select
    selectedOption={selectedRegion}
    onChange={({ detail }) => setSelectedRegion(detail.selectedOption)}
    options={[{ value: 'us-east-1', label: 'US East (N. Virginia)' }]}
    placeholder="Select a region"
  />
</FormField>

<FormField label="Servers">
  <Multiselect
    selectedOptions={selectedServers}
    onChange={({ detail }) => setSelectedServers(detail.selectedOptions)}
    options={servers.map(s => ({ value: s.id, label: s.hostname }))}
    filteringType="auto"
  />
</FormField>
```

### Form Actions
```typescript
<Form actions={
  <SpaceBetween direction="horizontal" size="xs">
    <Button variant="link" onClick={onCancel}>Cancel</Button>
    <Button variant="primary" loading={loading} onClick={onSubmit}>
      {isEdit ? 'Update' : 'Create'}
    </Button>
  </SpaceBetween>
}>
```

## Tables

### Table with Collection Hooks
```typescript
import { useCollection } from '@cloudscape-design/collection-hooks';

const { items, collectionProps, filterProps, paginationProps } = useCollection(data, {
  filtering: { empty: <EmptyState />, noMatch: <NoMatchState /> },
  pagination: { pageSize: 25 },
  sorting: { defaultState: { sortingColumn: { sortingField: 'name' }, isDescending: false } },
  selection: {},
});

<Table
  {...collectionProps}
  columnDefinitions={columnDefs}
  items={items}
  loading={loading}
  loadingText="Loading items..."
  header={<Header counter={`(${data.length})`} actions={<Button variant="primary">Create</Button>}>Items</Header>}
  filter={<TextFilter {...filterProps} filteringPlaceholder="Search items" />}
  pagination={<Pagination {...paginationProps} />}
  empty={<Box textAlign="center"><SpaceBetween size="m"><b>No items</b><Button onClick={onCreate}>Create</Button></SpaceBetween></Box>}
/>
```

## Modals

```typescript
<Modal
  visible={visible}
  onDismiss={onClose}
  header="Title"
  size="medium"  // small (300px), medium (600px), large (900px), max (1200px)
  footer={
    <Box float="right">
      <SpaceBetween direction="horizontal" size="xs">
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="primary" onClick={onSave}>Save</Button>
      </SpaceBetween>
    </Box>
  }
>
  {/* content */}
</Modal>
```

## Notifications

```typescript
// Flashbar (persistent, global)
const addNotification = (type: 'success' | 'error' | 'warning' | 'info', content: string) => {
  const id = Date.now().toString();
  setNotifications(prev => [...prev, {
    type, content, dismissible: true,
    onDismiss: () => removeNotification(id), id,
  }]);
  if (type === 'success') setTimeout(() => removeNotification(id), 5000);
};

// Alert (inline)
<Alert type="error" dismissible onDismiss={() => setError(null)}>{error}</Alert>
```

## Status Indicators

```typescript
<StatusIndicator type="success">Completed</StatusIndicator>
<StatusIndicator type="error">Failed</StatusIndicator>
<StatusIndicator type="warning">Warning</StatusIndicator>
<StatusIndicator type="pending">Pending</StatusIndicator>
<StatusIndicator type="in-progress">In Progress</StatusIndicator>

<Badge color="green">Active</Badge>
<Badge color="red">Inactive</Badge>
```

## Advanced Components

```typescript
// Wizard (multi-step)
<Wizard steps={[{ title: 'Step 1', content: <Step1 /> }]} onSubmit={handleCreate} onCancel={handleCancel} />

// AttributeEditor (key-value)
<AttributeEditor items={tags} onAddButtonClick={() => setTags([...tags, { key: '', value: '' }])}
  definition={[{ label: 'Key', control: item => <Input value={item.key} /> }]} />

// ExpandableSection
<ExpandableSection headerText="Advanced Options" defaultExpanded={false}>{/* content */}</ExpandableSection>

// KeyValuePairs
<KeyValuePairs columns={3} items={[{ label: 'Account ID', value: account.accountId }]} />

// Cards
<Cards items={groups} cardDefinition={{ header: item => item.name, sections: [{ id: 'count', header: 'Servers', content: item => item.serverCount }] }} />

// Popover
<Popover header="Help" content="Contextual help text" triggerType="custom"><StatusIndicator type="info">Info</StatusIndicator></Popover>
```

## Event Handling

All CloudScape events use the `detail` property:
```typescript
<Input onChange={({ detail }) => setValue(detail.value)} />
<Select onChange={({ detail }) => setSelected(detail.selectedOption)} />
<Checkbox onChange={({ detail }) => setChecked(detail.checked)} />
<Table onSelectionChange={({ detail }) => setSelected(detail.selectedItems)} />
<SideNavigation onFollow={(e) => { e.preventDefault(); navigate(e.detail.href); }} />
```

## CSS Architecture

### Design Tokens — ALWAYS Use Instead of Hardcoded Values

| Hardcoded | Token |
|-----------|-------|
| `#5f6b7a` | `var(--awsui-color-text-body-secondary)` |
| `#16191f` | `var(--awsui-color-text-body-default)` |
| `#0972d3` | `var(--awsui-color-text-link-default)` |
| `#037f0c` | `var(--awsui-color-text-status-success)` |
| `#d13212` | `var(--awsui-color-text-status-error)` |
| `#ffffff` | `var(--awsui-color-background-container-content)` |
| `8px` | `var(--awsui-space-scaled-xs)` |
| `16px` | `var(--awsui-space-scaled-m)` |
| `14px` | `var(--awsui-font-size-body-m)` |

### CSS Modules (Required Pattern)
```css
/* MyComponent.module.css */
.container {
  background-color: var(--awsui-color-background-container-content);
  border: 1px solid var(--awsui-color-border-container-top);
  border-radius: var(--awsui-border-radius-container);
  padding: var(--awsui-space-scaled-m);
}

.label {
  color: var(--awsui-color-text-label);
  font-size: var(--awsui-font-size-body-s);
  font-weight: var(--awsui-font-weight-bold);
}
```

```typescript
import styles from './MyComponent.module.css';
<div className={styles.container}><div className={styles.label}>Label</div></div>
```

### Styling Around CloudScape Components
```typescript
// CORRECT: Wrap in styled div
<div className={styles.actionContainer}><Button variant="primary">Save</Button></div>

// WRONG: className on CloudScape component (deprecated)
<Button className={styles.custom}>Save</Button>
```

### Z-Index Scale (Centralized)
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

### RTL Support — Use Logical Properties
```css
/* CORRECT */
.container { margin-inline-start: var(--awsui-space-scaled-m); text-align: start; }

/* WRONG */
.container { margin-left: 16px; text-align: left; }
```

### Dynamic Styling
```typescript
// CORRECT: CSS custom property
<div className={styles.bar} style={{ '--progress-width': `${progress}%` } as React.CSSProperties} />

// WRONG: inline style
<div style={{ width: `${progress}%` }} />
```

## Spacing Scale

`xxxs` (2px), `xxs` (4px), `xs` (8px), `s` (12px), `m` (16px), `l` (20px), `xl` (24px), `xxl` (32px)

```typescript
<SpaceBetween size="l">   {/* Between major sections */}
<SpaceBetween size="m">   {/* Between related items */}
<SpaceBetween size="s">   {/* Between form fields */}
<SpaceBetween size="xs">  {/* Between inline elements */}
```

## DRS Regions (30 Regions)

```typescript
const DRS_REGIONS = [
  // Americas (6)
  { value: 'us-east-1', label: 'us-east-1 (N. Virginia)' },
  { value: 'us-east-2', label: 'us-east-2 (Ohio)' },
  { value: 'us-west-1', label: 'us-west-1 (N. California)' },
  { value: 'us-west-2', label: 'us-west-2 (Oregon)' },
  { value: 'ca-central-1', label: 'ca-central-1 (Canada)' },
  { value: 'sa-east-1', label: 'sa-east-1 (São Paulo)' },
  // Europe (8)
  { value: 'eu-west-1', label: 'eu-west-1 (Ireland)' },
  { value: 'eu-west-2', label: 'eu-west-2 (London)' },
  { value: 'eu-west-3', label: 'eu-west-3 (Paris)' },
  { value: 'eu-central-1', label: 'eu-central-1 (Frankfurt)' },
  { value: 'eu-central-2', label: 'eu-central-2 (Zurich)' },
  { value: 'eu-north-1', label: 'eu-north-1 (Stockholm)' },
  { value: 'eu-south-1', label: 'eu-south-1 (Milan)' },
  { value: 'eu-south-2', label: 'eu-south-2 (Spain)' },
  // Asia Pacific (10)
  { value: 'ap-northeast-1', label: 'ap-northeast-1 (Tokyo)' },
  { value: 'ap-northeast-2', label: 'ap-northeast-2 (Seoul)' },
  { value: 'ap-northeast-3', label: 'ap-northeast-3 (Osaka)' },
  { value: 'ap-southeast-1', label: 'ap-southeast-1 (Singapore)' },
  { value: 'ap-southeast-2', label: 'ap-southeast-2 (Sydney)' },
  { value: 'ap-southeast-3', label: 'ap-southeast-3 (Jakarta)' },
  { value: 'ap-southeast-4', label: 'ap-southeast-4 (Melbourne)' },
  { value: 'ap-south-1', label: 'ap-south-1 (Mumbai)' },
  { value: 'ap-south-2', label: 'ap-south-2 (Hyderabad)' },
  { value: 'ap-east-1', label: 'ap-east-1 (Hong Kong)' },
  // Middle East & Africa (4)
  { value: 'me-south-1', label: 'me-south-1 (Bahrain)' },
  { value: 'me-central-1', label: 'me-central-1 (UAE)' },
  { value: 'af-south-1', label: 'af-south-1 (Cape Town)' },
  { value: 'il-central-1', label: 'il-central-1 (Tel Aviv)' },
  // GovCloud (2)
  { value: 'us-gov-east-1', label: 'us-gov-east-1 (GovCloud East)' },
  { value: 'us-gov-west-1', label: 'us-gov-west-1 (GovCloud West)' },
];
```

## Resources

- Components: https://cloudscape.design/components/
- Patterns: https://cloudscape.design/patterns/
- Design Tokens: https://cloudscape.design/foundation/visual-foundation/design-tokens/
- Collection Hooks: https://cloudscape.design/get-started/dev-guides/collection-hooks/
- Demos: https://cloudscape.design/demos/
