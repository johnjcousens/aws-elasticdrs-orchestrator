# Account Enforcement Feature Specification

## Overview
Implement account enforcement to ensure users must explicitly select a target account before using any DRS orchestration features. This prevents accidental operations on the wrong account and provides clear context about which account is being managed.

## Current State
- Application works but assumes target account without user selection
- All features are accessible regardless of account selection state
- Users can accidentally operate on wrong accounts
- No clear indication of which account context they're working in

## Requirements

### 1. Account Selection Enforcement
**User Story**: As a user, I want to be required to select a target account before I can use any DRS features, so I don't accidentally operate on the wrong account.

**Acceptance Criteria**:
- [ ] All DRS features (Protection Groups, Recovery Plans, Executions, Dashboard data) are disabled when no account is selected
- [ ] Clear messaging explains why features are disabled and how to select an account
- [ ] Account selection is persistent across browser sessions
- [ ] Account selection is clearly displayed in the UI header/navigation

### 2. Default Account Preference
**User Story**: As a user, I want to set a default account in settings so the app automatically selects it when I log in.

**Acceptance Criteria**:
- [ ] Settings → Account Management tab has a "Default Account" dropdown
- [ ] Default account preference is saved to localStorage
- [ ] Default account is automatically selected on app load (if it exists in available accounts)
- [ ] User can change or clear the default account preference
- [ ] Default account selection respects the enforcement rules

### 3. Single Account Auto-Selection
**User Story**: As a user with only one target account, I want it to be automatically selected so I don't have to manually select it every time.

**Acceptance Criteria**:
- [ ] If only 1 account exists, it's automatically set as selected (bypassing enforcement)
- [ ] Auto-selection happens after accounts are loaded
- [ ] Auto-selected account is treated as explicitly selected (features work normally)
- [ ] If user adds more accounts later, enforcement kicks in for future sessions

### 4. Account Selection UI
**User Story**: As a user, I want a clear way to select my target account and see which account I'm currently working with.

**Acceptance Criteria**:
- [ ] Account selector in the top navigation (next to user menu)
- [ ] Shows currently selected account name/ID
- [ ] Dropdown shows all available accounts
- [ ] Clear visual indication when no account is selected
- [ ] Account selection immediately enables/disables features

### 5. Feature Blocking Implementation
**User Story**: As a user, when no account is selected, I want to see helpful messages instead of broken features.

**Acceptance Criteria**:
- [ ] Dashboard shows "Select Account" message instead of loading data
- [ ] Protection Groups page shows account selection prompt
- [ ] Recovery Plans page shows account selection prompt  
- [ ] Executions page shows account selection prompt
- [ ] API calls are not made when no account is selected
- [ ] Navigation remains accessible (user can still access settings)

## Technical Implementation

### 1. AccountContext Modifications
```typescript
interface AccountContextType {
  // Existing properties...
  
  // New enforcement properties
  isAccountRequired: boolean;
  hasSelectedAccount: boolean;
  defaultAccountId: string | null;
  setDefaultAccountId: (accountId: string | null) => void;
  
  // Helper methods
  isFeatureEnabled: () => boolean;
  getAccountSelectionMessage: () => string;
}
```

### 2. Default Account Storage
- Use localStorage key: `drs-orchestration-default-account`
- Store account ID, not full account object
- Clear on logout or when account no longer exists

### 3. Account Selection Component
- New component: `AccountSelector` in top navigation
- Shows current account or "Select Account" prompt
- Dropdown with all available accounts
- Integrates with existing TopNavigation utilities

### 4. Feature Blocking Components
- Create `AccountRequiredWrapper` component for pages
- Shows account selection prompt when no account selected
- Allows normal content when account is selected
- Reusable across all protected pages

### 5. Settings Integration
- Add default account dropdown to existing AccountManagementPanel
- No new tabs - keep existing 3-tab structure
- Simple preference setting with clear explanation

## Implementation Steps

### Phase 1: Core Enforcement
1. Modify AccountContext to track selection state and default preference
2. Add localStorage persistence for default account
3. Implement auto-selection logic for single accounts
4. Add account enforcement checks

### Phase 2: UI Components  
1. Create AccountSelector component for navigation
2. Create AccountRequiredWrapper for page blocking
3. Integrate AccountSelector into TopNavigation
4. Update pages to use AccountRequiredWrapper

### Phase 3: Settings Integration
1. Add default account preference to AccountManagementPanel
2. Wire up default account selection logic
3. Test all scenarios (single account, multiple accounts, no accounts)

### Phase 4: Polish & Testing
1. Add proper loading states
2. Improve error messaging
3. Test account switching scenarios
4. Verify persistence across sessions

## Success Criteria
- [x] Users cannot access DRS features without selecting an account
- [x] Single account scenarios work seamlessly (auto-selected)
- [x] Multi-account scenarios require explicit selection
- [x] Default account preference works as expected
- [x] All existing functionality remains intact
- [x] Settings modal keeps original 3-tab structure
- [x] Clear user feedback for all states

## Risk Mitigation
- **Don't break existing features**: Test each change incrementally
- **Keep it simple**: Avoid complex state management or routing changes
- **Preserve working code**: Don't modify working components unnecessarily
- **Maintain 3-tab settings**: Don't change the settings modal structure
- **Test thoroughly**: Verify single account, multi-account, and no account scenarios

## Out of Scope
- Cross-account role management (already implemented)
- Account validation (already implemented)  
- Account creation/deletion (already implemented)
- Complex permission systems
- Account-specific feature restrictions