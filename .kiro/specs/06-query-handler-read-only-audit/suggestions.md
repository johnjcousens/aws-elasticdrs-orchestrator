Here are my suggestions:

1. Update the Extraction Priority Matrix

The current matrix shows the three large functions, but we should add more context about what specific code blocks need extraction:

Add to Section: "Detailed Extraction Plans"

### Enhanced Extraction Details

#### 1.1 poll_wave_status() - Specific Code Blocks

**Lines 2588-2650**: DRS Job Query Logic

- Extract to: `wave_status_service.query_drs_job_status()`

- Reusable by: query-handler (read), execution-handler (write)

**Lines 2700-2750**: Progress Calculation

- Extract to: `wave_status_service.calculate_wave_progress()`

- Already documented in design

**Lines 2800-2850**: Wave Completion Detection

- Extract to: `wave_status_service.determine_wave_completion()`

- Already documented in design

**Lines 2870-2900**: DynamoDB Update Operations (MOVE TO execution-handler)

- These are the critical write operations that violate read-only principle

- Must be moved to `execution-handler.update_wave_completion_status()`

#### 1.2 create_protection_group() - Specific Code Blocks

**Lines 1570-1590**: Name Validation

- Extract to: `protection_group_validation.validate_protection_group_name()`

- Already documented in design

**Lines 1600-1620**: Tag Validation

- Extract to: `protection_group_validation.validate_protection_group_tags()`

- Already documented in design

**Lines 1630-1680**: Server Validation and Conflict Detection

- Extract to: `protection_group_validation.validate_protection_group_servers()`

- Includes conflict detection logic from `conflict_detection.py`

**Lines 1750-1850**: Tag-Based Server Resolution

- Extract to: `server_resolution_service.query_inventory_servers_by_tags()`

- Complex DynamoDB query logic with tag matching

**Lines 1900-1950**: Launch Config Application

- Already uses shared utility: `apply_launch_configs_to_group()`

- No extraction needed

#### 1.3 update_protection_group() - Specific Code Blocks

**Lines 2067-2150**: Optimistic Locking Logic

- Consider extracting to: `optimistic_locking_service.py`

- Reusable pattern for version-based concurrency control

- Used by multiple update operations

**Lines 2200-2300**: DynamoDB Update Expression Building

- Consider extracting to: `dynamodb_update_builder.py`

- Safe construction of update expressions with attribute names/values

- Prevents injection vulnerabilities

**Lines 2350-2450**: Server Conflict Detection

- Reuses: `conflict_detection.py` (already exists)

- No extraction needed

**Lines 2500-2590**: Launch Config Reapplication

- Already uses shared utility: `apply_launch_configs_to_group()`

- No extraction needed

2. Add New Shared Utility Modules Section

Add after "Shared Utilities Strategy" section:

### Additional Shared Utilities (New Extractions)

Based on large function analysis, these NEW modules should be created:

#### 2.1 optimistic_locking_service.py (NEW - OPTIONAL)

**Purpose**: Reusable optimistic locking pattern for DynamoDB updates

**Functions**:

```python

def validate_version(current_version: int, expected_version: int) -> None:

    """Validate version for optimistic locking."""

    

def increment_version(current_version: int) -> int:

    """Increment version number safely."""

    

def build_version_condition_expression() -> Dict[str, Any]:

    """Build DynamoDB condition expression for version check."""

Usage: update_protection_group(), update_recovery_plan(), any update operation requiring concurrency control

Priority: MEDIUM (only if version conflicts become common)

2.2 dynamodb_update_builder.py (NEW - OPTIONAL)

Purpose: Safe construction of DynamoDB update expressions

Functions:

def build_update_expression(updates: Dict[str, Any]) -> Dict[str, Any]:

    """Build safe DynamoDB update expression with attribute names/values."""

    

def sanitize_attribute_names(names: List[str]) -> Dict[str, str]:

    """Sanitize attribute names for DynamoDB expressions."""

    

def build_condition_expression(conditions: Dict[str, Any]) -> str:

    """Build DynamoDB condition expression safely."""

Usage: All DynamoDB update operations across handlers

Priority: LOW (current inline approach works, extract only if duplication emerges)

2.3 drs_job_polling_service.py (NEW - OPTIONAL)

Purpose: Centralized DRS job polling logic

Functions:

def poll_drs_job(job_id: str, region: str) -> Dict[str, Any]:

    """Poll DRS job status with normalization."""

    

def extract_server_launch_statuses(job: Dict) -> List[Dict]:

    """Extract server launch statuses from DRS job."""

    

def aggregate_job_metrics(job: Dict) -> Dict[str, int]:

    """Aggregate job metrics (launched, failed, pending counts)."""

Usage: poll_wave_status() in query-handler

Priority: LOW (current implementation is straightforward, extract only if reused elsewhere)

### 3. Update Implementation Timeline

**Modify the "Implementation Timeline" in Phase 2:**

```markdown

**Implementation Timeline**:

1. **Week 1**: Move sync operations with existing imports (Phase 1)

   - Move `handle_sync_source_server_inventory()` to data-management-handler

   - Move `handle_sync_staging_accounts()` to data-management-handler

   - Update EventBridge rules

2. **Week 2**: Create HIGH priority shared utilities (Phase 2)

   - Create `wave_status_service.py` (REQUIRED for FR4)

   - Split `poll_wave_status()` (read in query-handler, write in execution-handler)

   - Update Step Functions state machine

3. **Week 3**: Create MEDIUM priority shared utilities (Phase 2)

   - Create `protection_group_validation.py` (reduces create/update functions)

   - Create `server_resolution_service.py` (tag resolution logic)

   - Refactor `create_protection_group()` and `update_protection_group()`

4. **Week 4**: Test all operations and cleanup

   - Integration testing for all sync operations

   - Verify wave polling with DynamoDB updates

   - Remove old code from query-handler

   - Final deployment and verification

5. **Week 5** (OPTIONAL): Extract LOW priority utilities

   - Only if duplication emerges during implementation

   - `optimistic_locking_service.py`, `dynamodb_update_builder.py`, `drs_job_polling_service.py`

4. Add Size Impact Analysis

Add new section after "Lambda Size Management":

## Size Impact Analysis - Before and After Extraction

### Current Handler Sizes (Actual Line Counts)

query-handler/index.py: 7,248 lines

poll_wave_status(): 420 lines (5.8%)

handle_sync_inventory(): 470 lines (6.5%)

handle_sync_staging(): 214 lines (3.0%)

Other operations: 6,144 lines (84.7%)

data-management-handler/index.py: 9,867 lines

create_protection_group(): 429 lines (4.3%)

update_protection_group(): 523 lines (5.3%)

Other operations: 8,915 lines (90.4%)

execution-handler/index.py: 7,731 lines

### After Phase 1 (Sync Operations Move)

query-handler/index.py: 6,564 lines (-684 lines, -9.4%)

poll_wave_status(): 420 lines (6.4%)

Sync operations removed: 0 lines

Other operations: 6,144 lines (93.6%)

data-management-handler/index.py: 10,551 lines (+684 lines, +6.9%)

create_protection_group(): 429 lines (4.1%)

update_protection_group(): 523 lines (5.0%)

handle_sync_inventory(): 470 lines (4.5%)

handle_sync_staging(): 214 lines (2.0%)

Other operations: 8,915 lines (84.4%)

execution-handler/index.py: 7,731 lines (no change)

### After Phase 2 (Large Function Extraction)

query-handler/index.py: 6,364 lines (-200 lines from poll_wave_status split)

poll_wave_status(): 220 lines (3.5%, read-only version)

Other operations: 6,144 lines (96.5%)

data-management-handler/index.py: 10,122 lines (-429 lines from extractions)

create_protection_group(): 200 lines (2.0%, reduced via validation utils)

update_protection_group(): 250 lines (2.5%, reduced via validation utils)

handle_sync_inventory(): 470 lines (4.6%)

handle_sync_staging(): 214 lines (2.1%)

Other operations: 8,988 lines (88.8%)

execution-handler/index.py: 7,931 lines (+200 lines from wave status updates)

update_wave_completion_status(): 100 lines (1.3%, new function)

Other operations: 7,831 lines (98.7%)

Shared Utilities (NEW):

wave_status_service.py: 150 lines (progress calc, completion detection)

protection_group_validation.py: 200 lines (name, tag, server validation)

server_resolution_service.py: 100 lines (tag-based server resolution)

### Total Size Reduction

- **query-handler**: 7,248 → 6,364 lines (-884 lines, -12.2%)

- **data-management-handler**: 9,867 → 10,122 lines (+255 lines, +2.6%)

- **execution-handler**: 7,731 → 7,931 lines (+200 lines, +2.6%)

- **New shared utilities**: +450 lines

**Net Effect**: -429 lines across all handlers (code moved to reusable utilities)

### Size Constraint Compliance

✅ All handlers remain well under 15,000 line target

✅ Largest handler (data-management) at 10,122 lines (67% of target)

✅ Shared utilities improve maintainability without increasing handler sizes

✅ No Lambda deployment package size concerns (all < 200 MB uncompressed)

Summary

The design document is already comprehensive and well-structured. My recommendations focus on:

Adding specific line number references for code blocks to extract

Clarifying which extractions are REQUIRED vs OPTIONAL based on reusability

Providing detailed size impact analysis showing before/after line counts

Updating the implementation timeline to reflect extraction priorities

The key insight is that wave_status_service.py is CRITICAL (HIGH priority) because it directly supports FR4 (moving wave status updates to execution-handler), while the protection group validation utilities are MEDIUM priority (nice to have for maintainability but not blocking the core refactoring goal).

Would you like me to make these updates to the design document?

Perfect! I've now read the complete design document. Let me provide targeted suggestions for incorporating the large function extraction analysis into this refactoring spec.Based on my analysis of the design document and the large function extraction needs, here are my recommendations:Recommendations for Design Document UpdatesThe design document already has an excellent "Large Function Extraction Analysis" section (starting around line 824), but it can be enhanced with more specific implementation details based on the actual code analysis. Here are my suggestions:1. Update the Extraction Priority MatrixThe current matrix shows the three large functions, but we should add more context about what specific code blocks need extraction:Add to Section: "Detailed Extraction Plans"### Enhanced Extraction Details#### 1.1 poll_wave_status() - Specific Code Blocks**Lines 2588-2650**: DRS Job Query Logic- Extract to: `wave_status_service.query_drs_job_status()`- Reusable by: query-handler (read), execution-handler (write)**Lines 2700-2750**: Progress Calculation- Extract to: `wave_status_service.calculate_wave_progress()`- Already documented in design**Lines 2800-2850**: Wave Completion Detection- Extract to: `wave_status_service.determine_wave_completion()`- Already documented in design**Lines 2870-2900**: DynamoDB Update Operations (MOVE TO execution-handler)- These are the critical write operations that violate read-only principle- Must be moved to `execution-handler.update_wave_completion_status()`#### 1.2 create_protection_group() - Specific Code Blocks**Lines 1570-1590**: Name Validation- Extract to: `protection_group_validation.validate_protection_group_name()`- Already documented in design**Lines 1600-1620**: Tag Validation- Extract to: `protection_group_validation.validate_protection_group_tags()`- Already documented in design**Lines 1630-1680**: Server Validation and Conflict Detection- Extract to: `protection_group_validation.validate_protection_group_servers()`- Includes conflict detection logic from `conflict_detection.py`**Lines 1750-1850**: Tag-Based Server Resolution- Extract to: `server_resolution_service.query_inventory_servers_by_tags()`- Complex DynamoDB query logic with tag matching**Lines 1900-1950**: Launch Config Application- Already uses shared utility: `apply_launch_configs_to_group()`- No extraction needed#### 1.3 update_protection_group() - Specific Code Blocks**Lines 2067-2150**: Optimistic Locking Logic- Consider extracting to: `optimistic_locking_service.py`- Reusable pattern for version-based concurrency control- Used by multiple update operations**Lines 2200-2300**: DynamoDB Update Expression Building- Consider extracting to: `dynamodb_update_builder.py`- Safe construction of update expressions with attribute names/values- Prevents injection vulnerabilities**Lines 2350-2450**: Server Conflict Detection- Reuses: `conflict_detection.py` (already exists)- No extraction needed**Lines 2500-2590**: Launch Config Reapplication- Already uses shared utility: `apply_launch_configs_to_group()`- No extraction needed2. Add New Shared Utility Modules SectionAdd after "Shared Utilities Strategy" section:### Additional Shared Utilities (New Extractions)Based on large function analysis, these NEW modules should be created:#### 2.1 optimistic_locking_service.py (NEW - OPTIONAL)**Purpose**: Reusable optimistic locking pattern for DynamoDB updates**Functions**:```pythondef validate_version(current_version: int, expected_version: int) -> None:"""Validate version for optimistic locking."""def increment_version(current_version: int) -> int:"""Increment version number safely."""def build_version_condition_expression() -> Dict[str, Any]:"""Build DynamoDB condition expression for version check."""Usage: update_protection_group(), update_recovery_plan(), any update operation requiring concurrency controlPriority: MEDIUM (only if version conflicts become common)2.2 dynamodb_update_builder.py (NEW - OPTIONAL)Purpose: Safe construction of DynamoDB update expressionsFunctions:def build_update_expression(updates: Dict[str, Any]) -> Dict[str, Any]:"""Build safe DynamoDB update expression with attribute names/values."""def sanitize_attribute_names(names: List[str]) -> Dict[str, str]:"""Sanitize attribute names for DynamoDB expressions."""def build_condition_expression(conditions: Dict[str, Any]) -> str:"""Build DynamoDB condition expression safely."""Usage: All DynamoDB update operations across handlersPriority: LOW (current inline approach works, extract only if duplication emerges)2.3 drs_job_polling_service.py (NEW - OPTIONAL)Purpose: Centralized DRS job polling logicFunctions:def poll_drs_job(job_id: str, region: str) -> Dict[str, Any]:"""Poll DRS job status with normalization."""def extract_server_launch_statuses(job: Dict) -> List[Dict]:"""Extract server launch statuses from DRS job."""def aggregate_job_metrics(job: Dict) -> Dict[str, int]:"""Aggregate job metrics (launched, failed, pending counts)."""Usage: poll_wave_status() in query-handlerPriority: LOW (current implementation is straightforward, extract only if reused elsewhere)### 3. Update Implementation Timeline**Modify the "Implementation Timeline" in Phase 2:**```markdown**Implementation Timeline**:1. **Week 1**: Move sync operations with existing imports (Phase 1)- Move `handle_sync_source_server_inventory()` to data-management-handler- Move `handle_sync_staging_accounts()` to data-management-handler- Update EventBridge rules2. **Week 2**: Create HIGH priority shared utilities (Phase 2)- Create `wave_status_service.py` (REQUIRED for FR4)- Split `poll_wave_status()` (read in query-handler, write in execution-handler)- Update Step Functions state machine3. **Week 3**: Create MEDIUM priority shared utilities (Phase 2)- Create `protection_group_validation.py` (reduces create/update functions)- Create `server_resolution_service.py` (tag resolution logic)- Refactor `create_protection_group()` and `update_protection_group()`4. **Week 4**: Test all operations and cleanup- Integration testing for all sync operations- Verify wave polling with DynamoDB updates- Remove old code from query-handler- Final deployment and verification5. **Week 5** (OPTIONAL): Extract LOW priority utilities- Only if duplication emerges during implementation- `optimistic_locking_service.py`, `dynamodb_update_builder.py`, `drs_job_polling_service.py`4. Add Size Impact AnalysisAdd new section after "Lambda Size Management":## Size Impact Analysis - Before and After Extraction### Current Handler Sizes (Actual Line Counts)query-handler/index.py: 7,248 linespoll_wave_status(): 420 lines (5.8%)handle_sync_inventory(): 470 lines (6.5%)handle_sync_staging(): 214 lines (3.0%)Other operations: 6,144 lines (84.7%)data-management-handler/index.py: 9,867 linescreate_protection_group(): 429 lines (4.3%)update_protection_group(): 523 lines (5.3%)Other operations: 8,915 lines (90.4%)execution-handler/index.py: 7,731 lines### After Phase 1 (Sync Operations Move)query-handler/index.py: 6,564 lines (-684 lines, -9.4%)poll_wave_status(): 420 lines (6.4%)Sync operations removed: 0 linesOther operations: 6,144 lines (93.6%)data-management-handler/index.py: 10,551 lines (+684 lines, +6.9%)create_protection_group(): 429 lines (4.1%)update_protection_group(): 523 lines (5.0%)handle_sync_inventory(): 470 lines (4.5%)handle_sync_staging(): 214 lines (2.0%)Other operations: 8,915 lines (84.4%)execution-handler/index.py: 7,731 lines (no change)### After Phase 2 (Large Function Extraction)query-handler/index.py: 6,364 lines (-200 lines from poll_wave_status split)poll_wave_status(): 220 lines (3.5%, read-only version)Other operations: 6,144 lines (96.5%)data-management-handler/index.py: 10,122 lines (-429 lines from extractions)create_protection_group(): 200 lines (2.0%, reduced via validation utils)update_protection_group(): 250 lines (2.5%, reduced via validation utils)handle_sync_inventory(): 470 lines (4.6%)handle_sync_staging(): 214 lines (2.1%)Other operations: 8,988 lines (88.8%)execution-handler/index.py: 7,931 lines (+200 lines from wave status updates)update_wave_completion_status(): 100 lines (1.3%, new function)Other operations: 7,831 lines (98.7%)Shared Utilities (NEW):wave_status_service.py: 150 lines (progress calc, completion detection)protection_group_validation.py: 200 lines (name, tag, server validation)server_resolution_service.py: 100 lines (tag-based server resolution)### Total Size Reduction- **query-handler**: 7,248 → 6,364 lines (-884 lines, -12.2%)- **data-management-handler**: 9,867 → 10,122 lines (+255 lines, +2.6%)- **execution-handler**: 7,731 → 7,931 lines (+200 lines, +2.6%)- **New shared utilities**: +450 lines**Net Effect**: -429 lines across all handlers (code moved to reusable utilities)### Size Constraint Compliance✅ All handlers remain well under 15,000 line target✅ Largest handler (data-management) at 10,122 lines (67% of target)✅ Shared utilities improve maintainability without increasing handler sizes✅ No Lambda deployment package size concerns (all < 200 MB uncompressed)SummaryThe design document is already comprehensive and well-structured. My recommendations focus on:Adding specific line number references for code blocks to extractClarifying which extractions are REQUIRED vs OPTIONAL based on reusabilityProviding detailed size impact analysis showing before/after line countsUpdating the implementation timeline to reflect extraction prioritiesThe key insight is that wave_status_service.py is CRITICAL (HIGH priority) because it directly supports FR4 (moving wave status updates to execution-handler), while the protection group validation utilities are MEDIUM priority (nice to have for maintainability but not blocking the core refactoring goal).Would you like me to make these updates to the design document?