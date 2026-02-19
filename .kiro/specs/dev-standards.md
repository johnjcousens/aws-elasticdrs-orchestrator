---
inclusion: always
---

# Development Standards

Consolidated coding standards for Python, TypeScript, and general technical practices.

## Python Standards (PEP 8)

### Critical Rules
- **Line length**: 79 characters maximum
- **Indentation**: 4 spaces (NO TABS)
- **String quotes**: Double quotes `"text"`
- **Imports**: Standard library → Third-party → Local

### Import Organization
```python
# 1. Standard library
import json
import os
from typing import Dict, List, Optional

# 2. Third-party
import boto3
from botocore.exceptions import ClientError

# 3. Local
from lambda.utils import format_response
```

### Type Hints (Required)
```python
def process_data(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process items and return summary."""
    pass
```

### Error Handling
```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
except Exception as e:
    logger.exception("Unexpected error")
    raise
```

### Logging
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Operation started")
logger.error("Operation failed", exc_info=True)
```

## TypeScript/Frontend Standards

### Critical Rules
- **Strict mode**: Always enabled
- **Type safety**: No `any` without justification
- **Naming**: PascalCase components, camelCase functions
- **File structure**: One component per file

### Component Structure
```typescript
// MyComponent.tsx
import React, { useState, useEffect } from 'react';
import { Button, Container } from '@cloudscape-design/components';

interface MyComponentProps {
  title: string;
  onSave: (data: Data) => void;
}

export const MyComponent: React.FC<MyComponentProps> = ({ title, onSave }) => {
  const [data, setData] = useState<Data | null>(null);
  
  useEffect(() => {
    // Effect logic
  }, []);
  
  return (
    <Container header={title}>
      {/* Component content */}
    </Container>
  );
};
```

### State Management
```typescript
// Use hooks for local state
const [value, setValue] = useState<string>('');

// Use context for global state
const { user, setUser } = useAuth();

// Use custom hooks for reusable logic
const { data, loading, error } = useFetchData(url);
```

### Error Boundaries
```typescript
class ErrorBoundary extends React.Component<Props, State> {
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    logError(error, errorInfo);
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorFallback />;
    }
    return this.props.children;
  }
}
```

## General Technical Standards

### Code Organization
```
project/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Page components
│   ├── hooks/          # Custom hooks
│   ├── utils/          # Utility functions
│   ├── types/          # TypeScript types
│   └── api/            # API client code
├── tests/              # Test files
└── docs/               # Documentation
```

### Naming Conventions
- **Files**: `kebab-case.ts`, `PascalCase.tsx` (components)
- **Variables**: `camelCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Classes**: `PascalCase`
- **Functions**: `camelCase`, verb-first (`getUserData`)

### Documentation
```python
def complex_function(param1: str, param2: int) -> Dict[str, Any]:
    """
    Brief description of what function does.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Dictionary containing results
        
    Raises:
        ValueError: If param2 is negative
    """
    pass
```

### Testing
```python
# Python - pytest
def test_user_creation():
    user = create_user("test@example.com")
    assert user.email == "test@example.com"
    assert user.is_active is True

# TypeScript - vitest
describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent title="Test" />);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });
});
```

### Performance
- **Lazy loading**: Use `React.lazy()` for code splitting
- **Memoization**: Use `useMemo` and `useCallback` appropriately
- **Debouncing**: Debounce expensive operations
- **Pagination**: Always paginate large lists

### Security
- **Input validation**: Validate all user input
- **SQL injection**: Use parameterized queries
- **XSS prevention**: Sanitize HTML output
- **Authentication**: Use secure token storage
- **HTTPS**: Always use HTTPS in production

## Quick Reference

### Python Checklist
- [ ] PEP 8 compliant (79 char lines, 4 spaces)
- [ ] Type hints on all functions
- [ ] Docstrings on public functions
- [ ] Proper error handling
- [ ] Logging instead of print()
- [ ] Tests written

### TypeScript Checklist
- [ ] Strict mode enabled
- [ ] No `any` types
- [ ] Props interface defined
- [ ] Error boundaries in place
- [ ] Accessibility attributes
- [ ] Tests written

### Code Review Checklist
- [ ] Follows naming conventions
- [ ] Properly documented
- [ ] Tests pass
- [ ] No security vulnerabilities
- [ ] Performance considered
- [ ] Error handling complete
