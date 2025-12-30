# Component Library

## AWS DRS Orchestration System

**Version**: 2.0  
**Date**: December 30, 2025  
**Status**: Production Ready

---

## Overview

This document specifies all 32 custom components required to build the AWS DRS Orchestration application. Each component must follow CloudScape design patterns and AWS Console conventions for consistent user experience.

---

## Layout Components (2)

### AppLayout (`cloudscape/AppLayout.tsx`)
**Build Requirements**: Create wrapper for CloudScape AppLayout component
- Must handle navigation, breadcrumbs, notifications
- Integrate with AuthContext and routing
- Provide consistent layout structure for all pages

### ContentLayout (`cloudscape/ContentLayout.tsx`)
**Build Requirements**: Create page content wrapper with header
- Must provide consistent spacing and structure
- Required by all protected pages
- Include proper CloudScape header integration

---

## Account Management (4)

### AccountSelector (`AccountSelector.tsx`)
**Build Requirements**: Create multi-account switching dropdown
- Must integrate with AccountContext
- Show current account or "Select Account" placeholder
- Handle account switching with proper state management

### AccountManagementPanel (`AccountManagementPanel.tsx`)
**Build Requirements**: Create complete account setup interface
- Must support add/edit/delete target accounts
- Include cross-account role configuration
- Provide validation and error handling

### AccountRequiredGuard (`AccountRequiredGuard.tsx`)
**Build Requirements**: Create conditional rendering component
- Must detect account configuration status
- Show setup instructions when no accounts configured
- Handle loading and error states

### AccountRequiredWrapper (`AccountRequiredWrapper.tsx`)
**Build Requirements**: Create wrapper for account-dependent features
- Must handle loading states and error conditions
- Provide fallback UI for missing account configuration
- Integrate with account management flow

---

## Server Management (4)

### ServerDiscoveryPanel (`ServerDiscoveryPanel.tsx`)
**Build Requirements**: Create DRS server discovery interface
- Must support discovery across all AWS regions
- Implement real-time search and filtering
- Include server selection with conflict detection

### ServerSelector (`ServerSelector.tsx`)
**Build Requirements**: Create tag-based server selection interface
- Must provide preview of selected servers
- Include validation and conflict checking
- Support multiple selection modes

### ServerListItem (`ServerListItem.tsx`)
**Build Requirements**: Create individual server display component
- Must show server details, status, region information
- Include action buttons for server operations
- Provide consistent server representation

### LaunchConfigSection (`LaunchConfigSection.tsx`)
**Build Requirements**: Create DRS launch configuration management
- Must handle instance type, subnet, security group settings
- Integrate with DRS API for configuration updates
- Provide form validation and error handling

---

## Dialog Components (4)

### ProtectionGroupDialog (`ProtectionGroupDialog.tsx`)
**Build Requirements**: Create protection group creation/editing modal
- Must include server discovery and selection
- Provide form validation and error handling
- Support both create and edit modes

### RecoveryPlanDialog (`RecoveryPlanDialog.tsx`)
**Build Requirements**: Create recovery plan creation/editing modal
- Must support wave configuration with dependencies
- Include pause point settings
- Provide validation for wave dependencies

### ConfirmDialog (`ConfirmDialog.tsx`)
**Build Requirements**: Create reusable confirmation dialog
- Must support customizable title, message, actions
- Include loading states for async operations
- Provide consistent confirmation pattern

### ImportResultsDialog (`ImportResultsDialog.tsx`)
**Build Requirements**: Create configuration import results display
- Must show success/failure summary
- Include detailed error reporting
- Provide clear feedback on import operations

---

## Configuration Management (2)

### ConfigExportPanel (`ConfigExportPanel.tsx`)
**Build Requirements**: Create configuration export interface
- Must export protection groups and recovery plans
- Support JSON format with metadata
- Include download functionality

### ConfigImportPanel (`ConfigImportPanel.tsx`)
**Build Requirements**: Create configuration import interface
- Must import configuration from JSON files
- Include validation and conflict resolution
- Support batch import with progress tracking

---

## Status & Progress (6)

### StatusBadge (`StatusBadge.tsx`)
**Build Requirements**: Create execution status display component
- Must map status to CloudScape badge types with colors
- Provide consistent status representation
- Support all execution status values

### InvocationSourceBadge (`InvocationSourceBadge.tsx`)
**Build Requirements**: Create execution source display component
- Must show execution source (UI, API, CLI, etc.)
- Include color-coded badges for different sources
- Provide tooltip with additional context

### WaveProgress (`WaveProgress.tsx`)
**Build Requirements**: Create wave-by-wave execution progress component
- Must show progress bars and status indicators
- Support real-time updates during execution
- Display wave completion status

### ExecutionDetails (`ExecutionDetails.tsx`)
**Build Requirements**: Create comprehensive execution information component
- Must display metadata, progress, wave details
- Integrate with real-time polling
- Support all execution states

### DRSQuotaStatus (`DRSQuotaStatus.tsx`)
**Build Requirements**: Create DRS service limits monitoring component
- Must show progress bars for capacity usage
- Support region-specific quota display
- Include real-time quota updates

### DateTimeDisplay (`DateTimeDisplay.tsx`)
**Build Requirements**: Create consistent date/time formatting component
- Must provide relative time display (e.g., "2 hours ago")
- Include timezone handling
- Support multiple date formats

---

## Form Components (2)

### WaveConfigEditor (`WaveConfigEditor.tsx`)
**Build Requirements**: Create wave configuration interface
- Must support protection group selection per wave
- Include pause point and dependency settings
- Provide validation for wave configuration

### RegionSelector (`RegionSelector.tsx`)
**Build Requirements**: Create AWS region selection dropdown
- Must include DRS-supported regions only (28 commercial regions)
- Show region display names and codes
- Support region filtering and search

---

## UI State Components (6)

### LoadingState (`LoadingState.tsx`)
**Build Requirements**: Create consistent loading indicators
- Must provide spinner with optional message
- Support different loading sizes
- Use across all async operations

### ErrorState (`ErrorState.tsx`)
**Build Requirements**: Create error display with retry options
- Must provide consistent error messaging
- Include retry functionality
- Integrate with error boundaries

### ErrorBoundary (`ErrorBoundary.tsx`)
**Build Requirements**: Create React error boundary implementation
- Must catch and display component errors
- Provide fallback UI for error recovery
- Include error reporting capabilities

### ErrorFallback (`ErrorFallback.tsx`)
**Build Requirements**: Create error boundary fallback component
- Must show user-friendly error messages
- Include reset functionality
- Provide error details when needed

### CardSkeleton (`CardSkeleton.tsx`)
**Build Requirements**: Create loading skeleton for card components
- Must match card layout structure
- Provide smooth loading transitions
- Support different card sizes

### DataTableSkeleton (`DataTableSkeleton.tsx`)
**Build Requirements**: Create loading skeleton for data tables
- Must match table structure
- Support configurable row count
- Provide realistic loading appearance

---

## Navigation & Routing (3)

### ProtectedRoute (`ProtectedRoute.tsx`)
**Build Requirements**: Create authentication guard for routes
- Must redirect to login if not authenticated
- Handle loading states during authentication check
- Support role-based access control

### PageTransition (`PageTransition.tsx`)
**Build Requirements**: Create smooth page transitions
- Must provide loading states between routes
- Include error handling for route changes
- Support transition animations

### SettingsModal (`SettingsModal.tsx`)
**Build Requirements**: Create application settings interface
- Must handle user preferences and configuration
- Provide modal-based settings panel
- Include settings persistence

---

## Component Implementation Patterns

### Required CloudScape Integration
All components must use CloudScape design system:
```typescript
import { Button, Modal, FormField } from '@cloudscape-design/components';
```

### Required Event Handling
CloudScape event pattern must be used:
```typescript
onChange={({ detail }) => setValue(detail.value)}
```

### Required Error Handling
Consistent error display pattern:
```typescript
{error && <Alert type="error">{error}</Alert>}
```

### Required Loading States
Standard loading pattern must be implemented:
```typescript
{loading ? <Spinner /> : <Content />}
```

---

## Build Requirements Summary

**Component Development**: Build all 32 components with the following requirements:
- CloudScape design system integration
- Consistent error handling and loading states
- Real-time updates and polling capabilities where needed
- TypeScript type safety throughout
- AWS Console-consistent user experience

---

## Development Guidelines

When building components:
1. Follow CloudScape design patterns exactly
2. Include proper TypeScript types for all props
3. Add error boundaries where appropriate
4. Implement loading states for async operations
5. Use consistent naming conventions
6. Ensure accessibility compliance
7. Include comprehensive error handling