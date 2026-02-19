# CloudScape Design System - Component Recommendations

**Date**: 2026-02-04  
**Purpose**: Identify CloudScape components to improve UX and reduce custom code  
**Reference**: https://cloudscape.design/components/

## Current Component Usage

### ✅ Already Using
- **Layout**: AppLayout, ContentLayout, Container, SpaceBetween, Grid
- **Data Display**: Table, StatusIndicator, Badge
- **Input**: Button, Input, Select, Multiselect, Textarea, Checkbox
- **Feedback**: Modal, Alert, Flashbar
- **Form**: Form, FormField

## Recommended Component Additions

### 1. Wizard Component
**Use Cases**:
- Protection Group creation (server selection → launch config → review)
- Recovery Plan creation (waves → dependencies → review)
- Target Account setup (credentials → validation → staging accounts)

**Benefits**:
- Guided multi-step workflows
- Built-in navigation and validation
- Progress indication

**Example**:
```tsx
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

### 2. AttributeEditor Component
**Use Cases**:
- Server selection tags (key-value pairs)
- Per-server launch template overrides
- Custom tags on protection groups
- Static IP assignments

**Benefits**:
- Built-in add/remove functionality
- Validation support
- Consistent UX for key-value editing

**Example**:
```tsx
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

### 3. ExpandableSection Component
**Use Cases**:
- Advanced launch configuration options
- Per-server configuration details
- Regional capacity breakdown
- Wave dependency configuration

**Benefits**:
- Reduces visual clutter
- Progressive disclosure
- Maintains context

**Example**:
```tsx
<ExpandableSection headerText="Advanced Options" defaultExpanded={false}>
  <FormField label="Instance Profile">
    <Select options={instanceProfiles} />
  </FormField>
  <FormField label="User Data">
    <Textarea />
  </FormField>
</ExpandableSection>
```

### 4. TokenGroup Component
**Use Cases**:
- Selected servers display
- Security group selection
- Subnet selection
- Tag filters

**Benefits**:
- Visual token representation
- Built-in removal
- Compact display

**Example**:
```tsx
<TokenGroup
  items={selectedServers.map(s => ({ label: s.hostname, dismissLabel: `Remove ${s.hostname}` }))}
  onDismiss={({ detail }) => removeServer(detail.itemIndex)}
/>
```

### 5. KeyValuePairs Component
**Use Cases**:
- Server details display
- Account information
- Execution metadata
- DRS configuration summary

**Benefits**:
- Consistent label-value layout
- Responsive design
- Copy-to-clipboard support

**Example**:
```tsx
<KeyValuePairs
  columns={3}
  items={[
    { label: 'Account ID', value: account.accountId },
    { label: 'Region', value: account.region },
    { label: 'Servers', value: account.serverCount }
  ]}
/>
```

### 6. Cards Component
**Use Cases**:
- Protection Group gallery view
- Recovery Plan selection
- Account capacity dashboard
- Server selection grid

**Benefits**:
- Visual card layout
- Selection support
- Responsive grid

**Example**:
```tsx
<Cards
  items={protectionGroups}
  cardDefinition={{
    header: item => item.groupName,
    sections: [
      { id: 'servers', header: 'Servers', content: item => `${item.serverCount} servers` },
      { id: 'region', header: 'Region', content: item => item.region },
      { id: 'status', content: item => <StatusIndicator type="success">Active</StatusIndicator> }
    ]
  }}
  onSelectionChange={({ detail }) => setSelected(detail.selectedItems)}
/>
```

### 7. Popover Component
**Use Cases**:
- Server status details
- Capacity warnings
- Help text
- Action confirmations

**Benefits**:
- Contextual information
- No modal interruption
- Positioning logic

**Example**:
```tsx
<Popover
  header="Capacity Warning"
  content="Region approaching 300-server limit"
  triggerType="custom"
>
  <StatusIndicator type="warning">High Capacity</StatusIndicator>
</Popover>
```

### 8. CodeEditor Component
**Use Cases**:
- Configuration export/import (JSON)
- User data scripts
- Launch template JSON
- API response debugging

**Benefits**:
- Syntax highlighting
- Line numbers
- Copy functionality

**Example**:
```tsx
<CodeEditor
  language="json"
  value={JSON.stringify(config, null, 2)}
  onChange={({ detail }) => setConfig(JSON.parse(detail.value))}
  preferences={{ theme: 'light' }}
/>
```

## Implementation Priority

### High Priority (Immediate Value)
1. **AttributeEditor** - Replace custom tag editors
2. **ExpandableSection** - Reduce form clutter
3. **TokenGroup** - Improve multi-select UX

### Medium Priority (Enhanced UX)
4. **Wizard** - Guided workflows for complex operations
5. **KeyValuePairs** - Consistent detail displays
6. **Popover** - Contextual help and warnings

### Low Priority (Nice to Have)
7. **Cards** - Alternative view for lists
8. **CodeEditor** - Advanced configuration editing

## Migration Strategy

### Phase 1: Low-Risk Replacements
- Replace custom tag displays with TokenGroup
- Add ExpandableSection to advanced options
- Use KeyValuePairs for detail views

### Phase 2: Form Enhancements
- Implement AttributeEditor for tag editing
- Add Popover for inline help
- Use ExpandableSection for optional fields

### Phase 3: Workflow Improvements
- Implement Wizard for Protection Group creation
- Implement Wizard for Recovery Plan creation
- Add Cards view for dashboard

### Phase 4: Advanced Features
- Add CodeEditor for JSON configuration
- Implement Cards for gallery views
- Add Popover for status details

## Component Reference

| Component | Documentation | Use Case |
|-----------|--------------|----------|
| Wizard | https://cloudscape.design/components/wizard/ | Multi-step workflows |
| AttributeEditor | https://cloudscape.design/components/attribute-editor/ | Key-value editing |
| ExpandableSection | https://cloudscape.design/components/expandable-section/ | Collapsible content |
| TokenGroup | https://cloudscape.design/components/token-group/ | Tag display |
| KeyValuePairs | https://cloudscape.design/components/key-value-pairs/ | Label-value pairs |
| Cards | https://cloudscape.design/components/cards/ | Card grid layout |
| Popover | https://cloudscape.design/components/popover/ | Contextual info |
| CodeEditor | https://cloudscape.design/components/code-editor/ | Code editing |

## Benefits Summary

### User Experience
- ✅ Consistent AWS Console UX patterns
- ✅ Reduced cognitive load (familiar components)
- ✅ Better accessibility (WCAG 2.1 AA compliant)
- ✅ Responsive design (mobile-friendly)

### Developer Experience
- ✅ Less custom code to maintain
- ✅ Built-in validation and error handling
- ✅ TypeScript support
- ✅ Comprehensive documentation

### Quality
- ✅ Battle-tested components (used in AWS Console)
- ✅ Regular updates and bug fixes
- ✅ Performance optimized
- ✅ Cross-browser compatibility

## Next Steps

1. Review recommendations with team
2. Prioritize components based on user feedback
3. Create implementation tasks for Phase 1
4. Update component library documentation
5. Add CloudScape examples to style guide
