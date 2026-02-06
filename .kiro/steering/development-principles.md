---
inclusion: always
---

# Development Principles

## Purpose
This document establishes core development philosophy and coding standards to prevent over-engineering, maintain code quality, and ensure focused, maintainable solutions.

## Core Philosophy
- **YAGNI (You Aren't Gonna Need It)**: The best code is no code. Don't add features we don't need right now
- **Simple over Clever**: We STRONGLY prefer simple, clean, maintainable solutions over clever or complex ones. Readability and maintainability are PRIMARY CONCERNS, even at the cost of conciseness or performance
- **Minimal Changes**: YOU MUST make the SMALLEST reasonable changes to achieve the desired outcome
- **No Over-Engineering**: Don't over-engineer a solution when a simple one is possible

## Change Management
- **Concentrated Changes**: Make focused, related changes in single commits to avoid creating too many changes
- **No Unrelated Changes**: YOU MUST NEVER make code changes unrelated to your current task. If you notice something that should be fixed but is unrelated, document it rather than fixing it immediately
- **Ask Before Rewriting**: YOU MUST ask permission before reimplementing features or systems from scratch instead of updating the existing implementation
- **Reduce Duplication**: YOU MUST WORK HARD to reduce code duplication, even if the refactoring takes extra effort

## Code Quality Standards
- **Match Existing Style**: YOU MUST MATCH the style and formatting of surrounding code, even if it differs from standard style guides. Consistency within a file trumps external standards
- **Preserve Comments**: YOU MUST NEVER remove code comments unless you can PROVE they are actively false. Comments are important documentation
- **Evergreen Comments**: Comments should describe the code as it is NOW, not what it used to do or how it changed
- **No Temporal References**: NEVER refer to temporal context in comments (like "recently refactored" "moved") or code
- **Value-Adding Comments**: Only include comments that explain WHY code exists or works a certain way, not WHAT it does (the code itself should be clear enough)

Examples of good comments:
```typescript
// Cache results to avoid expensive recalculations on subsequent calls
function memoizedCalculation() { ... }

// Timeout must be at least 1000ms to prevent race conditions with the database
const MIN_TIMEOUT = 1000;

// Handle edge case where the user has no permissions but needs to see error details
if (noPermissions && showErrorDetails) { ... }
```

Examples of bad comments:
```typescript
// Updated this function to use the new API
function getData() { ... }

// Moved from utils.js
function formatDate() { ... }

// This function gets data from the API
function fetchApiData() { ... }  // Redundant - name already says this
```
- **Avoid "New/Improved" Names**: If you name something "new" or "enhanced" or "improved", you've probably made a mistake

## Naming Conventions
- **Domain-Focused Names**: Names MUST tell what code does, not how it's implemented or its history
- **No Historical Context**: NEVER use temporal/historical context in names (e.g., "NewAPI", "LegacyHandler", "UnifiedTool")
