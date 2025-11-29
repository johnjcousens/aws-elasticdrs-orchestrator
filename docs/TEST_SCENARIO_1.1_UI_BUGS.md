# Test Scenario 1.1 - UI Display Bugs Discovered

**Date**: November 28, 2025, 4:52 PM EST  
**Update**: November 28, 2025, 8:10 PM EST - Deferred to next session  
**Screenshot**: test-screenshots/08-ui-display-bugs-discovered.png  
**Status**: 📋 **DOCUMENTED - DEFERRED** (Non-critical display issues)

## UI Bugs Found

### 1. Date/Time Display Issues
- **Problem**: Shows relative time ("1 hour ago", "16 hours ago") instead of actual timestamps
- **Expected**: Proper date/time formatting (e.g., "Nov 28, 2025 3:20 PM")
- **Impact**: Users can't see exact execution times

### 2. Wave Count Display
- **Problem**: Shows "0 waves" for completed executions that had waves
- **Expected**: Show actual wave count (e.g., "3 waves")
- **Impact**: Loss of important execution metadata

### 3. Status Display
- **Problem**: Shows "Unknown" status for some executions
- **Expected**: Show actual status (COMPLETED, POLLING, etc.)
- **Impact**: Users can't determine execution state

### 4. Duration Display
- **Problem**: Shows "0m" duration for all executions
- **Expected**: Show actual duration (e.g., "15m 30s")
- **Impact**: No visibility into execution time

### 5. Active Execution Not Visible
- **Problem**: Currently running execution (POLLING) not showing in list
- **Expected**: Real-time display of active executions
- **Impact**: Users can't monitor in-progress executions

## Root Causes (Likely)

### Frontend Data Parsing
- DateTimeDisplay component may not be handling DynamoDB timestamp format
- Wave count calculation may be failing
- Status field mapping issues
- Duration calculation not working

### Component Files to Check
- `frontend/src/components/DateTimeDisplay.tsx`
- `frontend/src/pages/ExecutionHistory.tsx` (if exists)
- Data fetching/parsing logic

## Combined Issues Summary

**Phase 1 Backend Bug**: Waves missing DRS Job IDs (CRITICAL - blocks completion)  
**UI Display Bugs**: 5 issues affecting data visibility (HIGH - impacts usability)

Both need fixing for production readiness.
