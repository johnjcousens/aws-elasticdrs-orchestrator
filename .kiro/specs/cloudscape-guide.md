---
inclusion: always
---

# CloudScape Quick Reference

Essential CloudScape Design System patterns for AWS Console-style UIs.

## Setup
```bash
npm install @cloudscape-design/components @cloudscape-design/global-styles
```

```typescript
// main.tsx
import '@cloudscape-design/global-styles/index.css';
```

## Core Layout

### AppLayout (Main Shell)
```typescript
<AppLayout
  navigation={<SideNavigation items={navItems} />}
  content={<YourContent />}
  breadcrumbs={<BreadcrumbGroup items={breadcrumbs} />}
  notifications={<Flashbar items={notifications} />}
/>
```

### ContentLayout (Page Wrapper)
```typescript
<ContentLayout
  header={
    <Header
      variant="h1"
      actions={<Button variant="primary">Create</Button>}
    >
      Page Title
    </Header>
  }
>
  <Container>{/* content */}</Container>
</ContentLayout>
```

### SpaceBetween (Spacing)
```typescript
<SpaceBetween direction="vertical" size="l">
  <Component1 />
  <Component2 />
</SpaceBetween>
```

## Forms

### FormField Pattern (Always Use)
```typescript
<FormField
  label="Name"
  description="Enter a unique name"
  errorText={errors.name}
>
  <Input
    value={name}
    onChange={({ detail }) => setName(detail.value)}
  />
</FormField>
```

### Common Inputs
```typescript
// Input
<Input value={text} onChange={({ detail }) => setText(detail.value)} />

// Select
<Select
  selectedOption={selected}
  onChange={({ detail }) => setSelected(detail.selectedOption)}
  options={[{ value: '1', label: 'Option 1' }]}
/>

// Multiselect
<Multiselect
  selectedOptions={selected}
  onChange={({ detail }) => setSelected(detail.selectedOptions)}
  options={options}
/>

// Textarea
<Textarea value={text} onChange={({ detail }) => setText(detail.value)} />

// Checkbox
<Checkbox checked={checked} onChange={({ detail }) => setChecked(detail.checked)}>
  Label
</Checkbox>
```

## Tables

### Table with Collection Hooks
```typescript
import { useCollection } from '@cloudscape-design/collection-hooks';

const { items, collectionProps, filterProps, paginationProps } = useCollection(
  data,
  {
    filtering: {},
    pagination: { pageSize: 25 },
    sorting: {},
    selection: {},
  }
);

<Table
  {...collectionProps}
  columnDefinitions={[
    {
      id: 'name',
      header: 'Name',
      cell: item => item.name,
      sortingField: 'name',
    },
  ]}
  items={items}
  filter={<TextFilter {...filterProps} />}
  pagination={<Pagination {...paginationProps} />}
/>
```

## Modals

### Modal Pattern
```typescript
<Modal
  visible={visible}
  onDismiss={onClose}
  header="Title"
  size="medium"
  footer={
    <Box float="right">
      <SpaceBetween direction="horizontal" size="xs">
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="primary" onClick={onSave}>Save</Button>
      </SpaceBetween>
    </Box>
  }
>
  {/* Modal content */}
</Modal>
```

**Sizes**: `small` (300px), `medium` (600px), `large` (900px), `max` (1200px)

## Notifications

### Flashbar (Global Notifications)
```typescript
const [notifications, setNotifications] = useState([]);

const addNotification = (type, content) => {
  const id = Date.now().toString();
  setNotifications(prev => [...prev, {
    type,  // 'success' | 'error' | 'warning' | 'info'
    content,
    dismissible: true,
    onDismiss: () => removeNotification(id),
    id,
  }]);
};

<Flashbar items={notifications} />
```

### Alert (Inline)
```typescript
<Alert type="error" dismissible onDismiss={() => setError(null)}>
  {error}
</Alert>
```

## Status Indicators

```typescript
<StatusIndicator type="success">Completed</StatusIndicator>
<StatusIndicator type="error">Failed</StatusIndicator>
<StatusIndicator type="warning">Warning</StatusIndicator>
<StatusIndicator type="pending">Pending</StatusIndicator>
<StatusIndicator type="in-progress">In Progress</StatusIndicator>
<StatusIndicator type="loading">Loading</StatusIndicator>

<Badge color="green">Active</Badge>
<Badge color="red">Inactive</Badge>

<ProgressBar value={75} label="Progress" status="in-progress" />
```

## Navigation

### SideNavigation
```typescript
<SideNavigation
  activeHref={location.pathname}
  items={[
    { type: 'link', text: 'Dashboard', href: '/' },
    { type: 'link', text: 'Items', href: '/items' },
    { type: 'divider' },
    { type: 'link', text: 'Settings', href: '/settings' },
  ]}
  onFollow={(e) => {
    e.preventDefault();
    navigate(e.detail.href);
  }}
/>
```

### Tabs
```typescript
<Tabs
  activeTabId={activeTab}
  onChange={({ detail }) => setActiveTab(detail.activeTabId)}
  tabs={[
    { id: 'tab1', label: 'Tab 1', content: <Content1 /> },
    { id: 'tab2', label: 'Tab 2', content: <Content2 /> },
  ]}
/>
```

## Common Patterns

### Loading State
```typescript
{loading ? (
  <Box textAlign="center" padding="xxl">
    <Spinner size="large" />
  </Box>
) : (
  <Content />
)}
```

### Empty State
```typescript
<Box textAlign="center" color="inherit">
  <SpaceBetween size="m">
    <b>No items</b>
    <Button variant="primary" onClick={onCreate}>Create</Button>
  </SpaceBetween>
</Box>
```

### Form Validation
```typescript
const [errors, setErrors] = useState({});

const validate = () => {
  const newErrors = {};
  if (!name) newErrors.name = 'Name is required';
  if (name.length < 3) newErrors.name = 'Min 3 characters';
  setErrors(newErrors);
  return Object.keys(newErrors).length === 0;
};
```

## Event Handling

All CloudScape events use `detail` property:

```typescript
<Input onChange={({ detail }) => setValue(detail.value)} />
<Select onChange={({ detail }) => setSelected(detail.selectedOption)} />
<Checkbox onChange={({ detail }) => setChecked(detail.checked)} />
<Table onSelectionChange={({ detail }) => setSelected(detail.selectedItems)} />
```

## Accessibility

```typescript
<Button iconName="edit" ariaLabel="Edit item" />
<Input ariaLabel="Search items" placeholder="Search..." />
```

## Advanced Components

### Wizard (Multi-Step Workflows)
```typescript
<Wizard
  steps={[
    { title: 'Select Servers', content: <ServerSelection /> },
    { title: 'Launch Configuration', content: <LaunchConfig /> },
    { title: 'Review', content: <Review /> }
  ]}
  onSubmit={handleCreate}
  onCancel={handleCancel}
/>
```

### AttributeEditor (Key-Value Editing)
```typescript
<AttributeEditor
  items={tags}
  onAddButtonClick={() => setTags([...tags, { key: '', value: '' }])}
  onRemoveButtonClick={({ detail }) => 
    setTags(tags.filter((_, i) => i !== detail.itemIndex))
  }
  definition={[
    { label: 'Key', control: item => <Input value={item.key} /> },
    { label: 'Value', control: item => <Input value={item.value} /> }
  ]}
/>
```

### ExpandableSection (Progressive Disclosure)
```typescript
<ExpandableSection headerText="Advanced Options" defaultExpanded={false}>
  <FormField label="Instance Profile">
    <Select options={instanceProfiles} />
  </FormField>
</ExpandableSection>
```

### TokenGroup (Tag Display)
```typescript
<TokenGroup
  items={selectedServers.map(s => ({ 
    label: s.hostname, 
    dismissLabel: `Remove ${s.hostname}` 
  }))}
  onDismiss={({ detail }) => removeServer(detail.itemIndex)}
/>
```

### KeyValuePairs (Detail Display)
```typescript
<KeyValuePairs
  columns={3}
  items={[
    { label: 'Account ID', value: account.accountId },
    { label: 'Region', value: account.region },
    { label: 'Servers', value: account.serverCount }
  ]}
/>
```

### Popover (Contextual Help)
```typescript
<Popover
  header="Capacity Warning"
  content="Region approaching 300-server limit"
  triggerType="custom"
>
  <StatusIndicator type="warning">High Capacity</StatusIndicator>
</Popover>
```

### Cards (Gallery View)
```typescript
<Cards
  items={protectionGroups}
  cardDefinition={{
    header: item => item.groupName,
    sections: [
      { id: 'servers', header: 'Servers', content: item => `${item.serverCount} servers` },
      { id: 'region', header: 'Region', content: item => item.region }
    ]
  }}
  onSelectionChange={({ detail }) => setSelected(detail.selectedItems)}
/>
```

### CodeEditor (JSON Editing)
```typescript
<CodeEditor
  language="json"
  value={JSON.stringify(config, null, 2)}
  onChange={({ detail }) => setConfig(JSON.parse(detail.value))}
  preferences={{ theme: 'light' }}
/>
```

## Resources

- Components: https://cloudscape.design/components/
- Patterns: https://cloudscape.design/patterns/
- Collection Hooks: https://cloudscape.design/get-started/dev-guides/collection-hooks/
