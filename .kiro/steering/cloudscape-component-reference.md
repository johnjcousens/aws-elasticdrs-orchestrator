---
inclusion: manual
---

# CloudScape Component Reference

## Purpose
Quick reference guide for CloudScape components used in AWS DRS Orchestration frontend migration.

## Layout Components

### AppLayout
Main application layout with navigation, content, and tools.

```typescript
import { AppLayout } from '@cloudscape-design/components';

<AppLayout
  navigation={<SideNavigation />}
  content={<YourContent />}
  breadcrumbs={<BreadcrumbGroup />}
  notifications={<Flashbar />}
  tools={<HelpPanel />}
  toolsHide={false}
  navigationHide={false}
  navigationWidth={280}
  contentType="default"
/>
```

**Props:**
- `navigation` - Side navigation component
- `content` - Main content area
- `breadcrumbs` - Breadcrumb navigation
- `notifications` - Flashbar for notifications
- `tools` - Help panel (optional)
- `toolsHide` - Hide tools panel
- `navigationHide` - Hide navigation panel

### ContentLayout
Page content wrapper with header.

```typescript
import { ContentLayout, Header } from '@cloudscape-design/components';

<ContentLayout
  header={
    <Header
      variant="h1"
      description="Page description"
      actions={<Button>Action</Button>}
    >
      Page Title
    </Header>
  }
>
  <Container>Content</Container>
</ContentLayout>
```

### SpaceBetween
Consistent spacing between elements.

```typescript
import { SpaceBetween } from '@cloudscape-design/components';

<SpaceBetween direction="vertical" size="l">
  <Component1 />
  <Component2 />
</SpaceBetween>
```

**Sizes:** `xxxs`, `xxs`, `xs`, `s`, `m`, `l`, `xl`, `xxl`

### ColumnLayout
Responsive column layout.

```typescript
import { ColumnLayout } from '@cloudscape-design/components';

<ColumnLayout columns={3} variant="text-grid">
  <div>Column 1</div>
  <div>Column 2</div>
  <div>Column 3</div>
</ColumnLayout>
```

**Variants:** `default`, `text-grid`

### Container
Content container with optional header/footer.

```typescript
import { Container, Header } from '@cloudscape-design/components';

<Container
  header={<Header variant="h2">Section Title</Header>}
  footer="Footer content"
>
  Container content
</Container>
```

### Box
Generic container with utility props.

```typescript
import { Box } from '@cloudscape-design/components';

<Box
  padding="l"
  margin="m"
  textAlign="center"
  color="text-status-error"
>
  Content
</Box>
```

## Form Components

### FormField
Wrapper for form inputs with label and error.

```typescript
import { FormField, Input } from '@cloudscape-design/components';

<FormField
  label="Field Label"
  description="Helper text"
  errorText={error}
  constraintText="Constraint text"
  stretch={true}
>
  <Input value={value} onChange={onChange} />
</FormField>
```

### Input
Text input field.

```typescript
import { Input } from '@cloudscape-design/components';

<Input
  value={value}
  onChange={({ detail }) => setValue(detail.value)}
  placeholder="Enter text"
  type="text"
  disabled={false}
  readOnly={false}
  invalid={false}
  ariaLabel="Input label"
/>
```

**Types:** `text`, `password`, `email`, `number`, `search`, `url`

### Textarea
Multi-line text input.

```typescript
import { Textarea } from '@cloudscape-design/components';

<Textarea
  value={value}
  onChange={({ detail }) => setValue(detail.value)}
  placeholder="Enter text"
  rows={4}
  disabled={false}
/>
```

### Select
Dropdown selection.

```typescript
import { Select } from '@cloudscape-design/components';

<Select
  selectedOption={{ value: 'option1', label: 'Option 1' }}
  onChange={({ detail }) => setSelected(detail.selectedOption)}
  options={[
    { value: 'option1', label: 'Option 1' },
    { value: 'option2', label: 'Option 2' },
  ]}
  placeholder="Select an option"
  disabled={false}
  invalid={false}
/>
```

### Multiselect
Multiple selection dropdown.

```typescript
import { Multiselect } from '@cloudscape-design/components';

<Multiselect
  selectedOptions={selectedOptions}
  onChange={({ detail }) => setSelectedOptions(detail.selectedOptions)}
  options={[
    { value: 'option1', label: 'Option 1' },
    { value: 'option2', label: 'Option 2' },
  ]}
  placeholder="Select options"
/>
```

### Checkbox
Single checkbox.

```typescript
import { Checkbox } from '@cloudscape-design/components';

<Checkbox
  checked={checked}
  onChange={({ detail }) => setChecked(detail.checked)}
  disabled={false}
>
  Checkbox label
</Checkbox>
```

### RadioGroup
Radio button group.

```typescript
import { RadioGroup } from '@cloudscape-design/components';

<RadioGroup
  value={value}
  onChange={({ detail }) => setValue(detail.value)}
  items={[
    { value: 'option1', label: 'Option 1' },
    { value: 'option2', label: 'Option 2' },
  ]}
/>
```

### Toggle
On/off switch.

```typescript
import { Toggle } from '@cloudscape-design/components';

<Toggle
  checked={checked}
  onChange={({ detail }) => setChecked(detail.checked)}
  disabled={false}
>
  Toggle label
</Toggle>
```

### DatePicker
Date selection.

```typescript
import { DatePicker } from '@cloudscape-design/components';

<DatePicker
  value={value}
  onChange={({ detail }) => setValue(detail.value)}
  placeholder="YYYY/MM/DD"
  disabled={false}
  invalid={false}
/>
```

### Form
Form container with actions.

```typescript
import { Form, SpaceBetween, Button } from '@cloudscape-design/components';

<Form
  actions={
    <SpaceBetween direction="horizontal" size="xs">
      <Button>Cancel</Button>
      <Button variant="primary">Submit</Button>
    </SpaceBetween>
  }
>
  <SpaceBetween direction="vertical" size="l">
    <FormField label="Field 1">
      <Input value={value1} onChange={onChange1} />
    </FormField>
    <FormField label="Field 2">
      <Input value={value2} onChange={onChange2} />
    </FormField>
  </SpaceBetween>
</Form>
```

## Button Components

### Button
Standard button.

```typescript
import { Button } from '@cloudscape-design/components';

<Button
  variant="primary"
  onClick={handleClick}
  disabled={false}
  loading={false}
  iconName="add-plus"
  iconAlign="left"
  ariaLabel="Button label"
>
  Button Text
</Button>
```

**Variants:** `primary`, `normal`, `link`, `icon`

### ButtonDropdown
Button with dropdown menu.

```typescript
import { ButtonDropdown } from '@cloudscape-design/components';

<ButtonDropdown
  items={[
    { id: 'action1', text: 'Action 1' },
    { id: 'action2', text: 'Action 2' },
  ]}
  onItemClick={({ detail }) => handleAction(detail.id)}
>
  Actions
</ButtonDropdown>
```

## Table Components

### Table
Data table with sorting, filtering, pagination.

```typescript
import { Table, TextFilter, Pagination } from '@cloudscape-design/components';
import { useCollection } from '@cloudscape-design/collection-hooks';

const { items, collectionProps, filterProps, paginationProps } = useCollection(
  allItems,
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
      cell: (item) => item.name,
      sortingField: 'name',
      width: 200,
    },
  ]}
  items={items}
  loading={loading}
  loadingText="Loading..."
  empty={<EmptyState />}
  filter={<TextFilter {...filterProps} />}
  pagination={<Pagination {...paginationProps} />}
  preferences={<CollectionPreferences />}
  selectionType="multi"
  selectedItems={selectedItems}
  onSelectionChange={({ detail }) => setSelectedItems(detail.selectedItems)}
/>
```

### TextFilter
Search/filter input for tables.

```typescript
import { TextFilter } from '@cloudscape-design/components';

<TextFilter
  filteringText={filteringText}
  onChange={({ detail }) => setFilteringText(detail.filteringText)}
  filteringPlaceholder="Search items"
  countText={`${filteredCount} matches`}
/>
```

### Pagination
Table pagination controls.

```typescript
import { Pagination } from '@cloudscape-design/components';

<Pagination
  currentPageIndex={currentPageIndex}
  pagesCount={pagesCount}
  onChange={({ detail }) => setCurrentPageIndex(detail.currentPageIndex)}
  ariaLabels={{
    nextPageLabel: 'Next page',
    previousPageLabel: 'Previous page',
    pageLabel: (pageNumber) => `Page ${pageNumber}`,
  }}
/>
```

### CollectionPreferences
Table preferences (columns, page size).

```typescript
import { CollectionPreferences } from '@cloudscape-design/components';

<CollectionPreferences
  title="Preferences"
  confirmLabel="Confirm"
  cancelLabel="Cancel"
  preferences={preferences}
  onConfirm={({ detail }) => setPreferences(detail)}
  pageSizePreference={{
    title: 'Page size',
    options: [
      { value: 10, label: '10 items' },
      { value: 25, label: '25 items' },
      { value: 50, label: '50 items' },
    ],
  }}
  visibleContentPreference={{
    title: 'Visible columns',
    options: [
      { id: 'name', label: 'Name' },
      { id: 'status', label: 'Status' },
    ],
  }}
/>
```

## Modal Components

### Modal
Dialog/modal window.

```typescript
import { Modal, Box, SpaceBetween, Button } from '@cloudscape-design/components';

<Modal
  visible={visible}
  onDismiss={onDismiss}
  header="Modal Title"
  size="medium"
  footer={
    <Box float="right">
      <SpaceBetween direction="horizontal" size="xs">
        <Button variant="link" onClick={onDismiss}>Cancel</Button>
        <Button variant="primary" onClick={onSave}>Save</Button>
      </SpaceBetween>
    </Box>
  }
>
  Modal content
</Modal>
```

**Sizes:** `small`, `medium`, `large`, `max`

## Notification Components

### Flashbar
Stack of notifications.

```typescript
import { Flashbar } from '@cloudscape-design/components';

<Flashbar
  items={[
    {
      type: 'success',
      content: 'Operation successful',
      dismissible: true,
      onDismiss: () => removeNotification(id),
      id: 'notification-1',
    },
  ]}
/>
```

**Types:** `success`, `error`, `warning`, `info`

### Alert
Inline alert message.

```typescript
import { Alert } from '@cloudscape-design/components';

<Alert
  type="error"
  dismissible
  onDismiss={() => setError(null)}
  header="Error occurred"
>
  Error message details
</Alert>
```

## Status Components

### Badge
Status badge.

```typescript
import { Badge } from '@cloudscape-design/components';

<Badge color="green">Active</Badge>
```

**Colors:** `blue`, `grey`, `green`, `red`

### StatusIndicator
Status with icon.

```typescript
import { StatusIndicator } from '@cloudscape-design/components';

<StatusIndicator type="success">Success</StatusIndicator>
```

**Types:** `success`, `error`, `warning`, `info`, `stopped`, `pending`, `in-progress`, `loading`

### ProgressBar
Progress indicator.

```typescript
import { ProgressBar } from '@cloudscape-design/components';

<ProgressBar
  value={75}
  label="Progress"
  description="75% complete"
  status="in-progress"
/>
```

**Status:** `success`, `error`, `in-progress`

### Spinner
Loading spinner.

```typescript
import { Spinner } from '@cloudscape-design/components';

<Spinner size="large" />
```

**Sizes:** `normal`, `big`, `large`

## Navigation Components

### SideNavigation
Side navigation menu.

```typescript
import { SideNavigation } from '@cloudscape-design/components';

<SideNavigation
  activeHref="/protection-groups"
  items={[
    { type: 'link', text: 'Dashboard', href: '/' },
    { type: 'link', text: 'Protection Groups', href: '/protection-groups' },
    { type: 'divider' },
    { type: 'link', text: 'Settings', href: '/settings' },
  ]}
  onFollow={(event) => {
    event.preventDefault();
    navigate(event.detail.href);
  }}
/>
```

### TopNavigation
Top navigation bar.

```typescript
import { TopNavigation } from '@cloudscape-design/components';

<TopNavigation
  identity={{
    href: '/',
    title: 'AWS DRS Orchestration',
  }}
  utilities={[
    {
      type: 'button',
      text: 'Documentation',
      href: '/docs',
    },
    {
      type: 'menu-dropdown',
      text: 'User',
      items: [
        { id: 'profile', text: 'Profile' },
        { id: 'logout', text: 'Logout' },
      ],
    },
  ]}
/>
```

### BreadcrumbGroup
Breadcrumb navigation.

```typescript
import { BreadcrumbGroup } from '@cloudscape-design/components';

<BreadcrumbGroup
  items={[
    { text: 'Home', href: '/' },
    { text: 'Protection Groups', href: '/protection-groups' },
    { text: 'Edit', href: '/protection-groups/edit' },
  ]}
  onFollow={(event) => {
    event.preventDefault();
    navigate(event.detail.href);
  }}
/>
```

### Tabs
Tab navigation.

```typescript
import { Tabs } from '@cloudscape-design/components';

<Tabs
  activeTabId={activeTabId}
  onChange={({ detail }) => setActiveTabId(detail.activeTabId)}
  tabs={[
    { id: 'tab1', label: 'Tab 1', content: <Tab1Content /> },
    { id: 'tab2', label: 'Tab 2', content: <Tab2Content /> },
  ]}
/>
```

## Display Components

### Header
Section header.

```typescript
import { Header } from '@cloudscape-design/components';

<Header
  variant="h1"
  description="Header description"
  actions={<Button>Action</Button>}
  counter="(10)"
>
  Header Title
</Header>
```

**Variants:** `h1`, `h2`, `h3`

### Link
Hyperlink.

```typescript
import { Link } from '@cloudscape-design/components';

<Link
  href="/path"
  external={false}
  variant="primary"
  onFollow={(event) => {
    event.preventDefault();
    navigate(event.detail.href);
  }}
>
  Link text
</Link>
```

### Icon
Icon display.

```typescript
import { Icon } from '@cloudscape-design/components';

<Icon name="settings" size="medium" variant="normal" />
```

### Popover
Tooltip/popover.

```typescript
import { Popover } from '@cloudscape-design/components';

<Popover
  header="Popover header"
  content="Popover content"
  dismissButton={false}
  position="top"
  size="medium"
>
  <Button iconName="status-info" variant="icon" />
</Popover>
```

## Progress Components

### ProgressIndicator
Step progress indicator.

```typescript
import { ProgressIndicator } from '@cloudscape-design/components';

<ProgressIndicator
  currentStepIndex={1}
  steps={[
    { label: 'Step 1', description: 'Description 1' },
    { label: 'Step 2', description: 'Description 2' },
    { label: 'Step 3', description: 'Description 3' },
  ]}
/>
```

### Wizard
Multi-step wizard.

```typescript
import { Wizard } from '@cloudscape-design/components';

<Wizard
  activeStepIndex={activeStepIndex}
  onNavigate={({ detail }) => setActiveStepIndex(detail.requestedStepIndex)}
  steps={[
    {
      title: 'Step 1',
      content: <Step1Content />,
    },
    {
      title: 'Step 2',
      content: <Step2Content />,
    },
  ]}
  onSubmit={handleSubmit}
  onCancel={handleCancel}
/>
```

## Utility Components

### TokenGroup
Tag/token group.

```typescript
import { TokenGroup } from '@cloudscape-design/components';

<TokenGroup
  items={[
    { label: 'Tag 1', dismissLabel: 'Remove Tag 1' },
    { label: 'Tag 2', dismissLabel: 'Remove Tag 2' },
  ]}
  onDismiss={({ detail }) => removeTag(detail.itemIndex)}
/>
```

### KeyValuePairs
Key-value display.

```typescript
import { KeyValuePairs } from '@cloudscape-design/components';

<KeyValuePairs
  columns={2}
  items={[
    { label: 'Name', value: 'Value 1' },
    { label: 'Status', value: 'Active' },
  ]}
/>
```

### ExpandableSection
Collapsible section.

```typescript
import { ExpandableSection } from '@cloudscape-design/components';

<ExpandableSection
  header="Section header"
  defaultExpanded={false}
  variant="container"
>
  Section content
</ExpandableSection>
```

## Event Handling

All CloudScape components use `detail` property in events:

```typescript
// Input
onChange={({ detail }) => setValue(detail.value)}

// Select
onChange={({ detail }) => setSelected(detail.selectedOption)}

// Checkbox
onChange={({ detail }) => setChecked(detail.checked)}

// Table selection
onSelectionChange={({ detail }) => setSelected(detail.selectedItems)}

// Button click
onClick={({ detail }) => handleClick()}
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

### Error State
```typescript
{error && (
  <Alert type="error" dismissible onDismiss={() => setError(null)}>
    {error}
  </Alert>
)}
```

### Empty State
```typescript
<Box textAlign="center" color="inherit">
  <SpaceBetween size="m">
    <b>No items</b>
    <Button onClick={handleCreate}>Create item</Button>
  </SpaceBetween>
</Box>
```

## Resources

- Component Documentation: https://cloudscape.design/components/
- Component Playground: https://cloudscape.design/playground/
- Design Patterns: https://cloudscape.design/patterns/
