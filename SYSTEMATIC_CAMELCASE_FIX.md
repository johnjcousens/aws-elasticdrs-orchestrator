# Systematic CamelCase Migration Fix

## ROOT CAUSE ANALYSIS
The migration was incomplete - it changed some field names but not others, creating a mixed state that breaks everything.

## WORKING v1.3.0 PATTERN
- **Database**: PascalCase fields (GroupId, GroupName, Version, LastModifiedDate)
- **API Input**: PascalCase fields (GroupName, SourceServerIds, ServerSelectionTags)
- **API Output**: camelCase via transform_pg_to_camelcase() function
- **Update Expression**: Simple string concatenation

## CURRENT BROKEN STATE
- **Database**: Mixed PascalCase/camelCase causing field mismatches
- **API Input**: Mixed camelCase/PascalCase validation
- **API Output**: No transform function, expects raw camelCase
- **Update Expression**: Tries to use undefined set_clauses array

## COMPLETE FIX REQUIRED

### Option 1: Complete camelCase Migration (RECOMMENDED)
1. **Database Operations**: Use camelCase throughout (groupId, groupName, version, lastModifiedDate)
2. **API Input Validation**: Expect camelCase fields (groupName, sourceServerIds, serverSelectionTags)
3. **API Output**: Return raw database fields (no transform needed)
4. **Update Expression**: Use string concatenation pattern

### Option 2: Revert to v1.3.0 Working State
1. **Database Operations**: Use PascalCase throughout (GroupId, GroupName, Version, LastModifiedDate)
2. **API Input Validation**: Expect PascalCase fields (GroupName, SourceServerIds, ServerSelectionTags)
3. **API Output**: Use transform_pg_to_camelcase() function
4. **Update Expression**: Use string concatenation pattern

## SYSTEMATIC ISSUES TO FIX

### 1. Database Field References
- Line 2334: `Key={"groupId": group_id}` should be consistent
- Line 2337: `existing_group.get("version", 1)` should be consistent
- Line 2695: `"Key": {"groupId": group_id}` should be consistent
- Line 2697: `"ConditionExpression": "version = :current_version"` should be consistent

### 2. API Input Field Validation
- Line 2378: `if "groupName" in body:` should be consistent
- Line 2379: `name = body["groupName"]` should be consistent
- Line 2408: `body["groupName"] = name.strip()` should be consistent
- Line 2412: `if body["groupName"] != existing_group.get("groupName"):` should be consistent

### 3. Update Expression Building
- Line 2610: `set_clauses.append("launchConfig = :launchConfig")` - UNDEFINED VARIABLE
- Should use: `update_expression += ", launchConfig = :launchConfig"`

### 4. Response Transformation
- Missing transform function or raw field return consistency

## IMPLEMENTATION PLAN
1. Choose Option 1 (Complete camelCase) for performance
2. Fix ALL database field references to use camelCase
3. Fix ALL API input validation to expect camelCase
4. Fix update expression to use string concatenation
5. Return raw database fields (no transform needed)
6. Test all CRUD operations end-to-end