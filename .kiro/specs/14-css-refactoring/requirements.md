# Requirements Document: CSS Refactoring

## Introduction

This specification defines the requirements for refactoring custom CSS in the AWS DRS Orchestration frontend application to align with official AWS design standards and CloudScape Design System guidelines. The current implementation contains extensive inline styles scattered throughout components (50+ instances), hardcoded color and spacing values, and inconsistent use of CloudScape Design System tokens. This refactoring will establish a maintainable, scalable CSS architecture that leverages CloudScape's comprehensive design token system while ensuring compliance with AWS Management Console visual standards.

### AWS Design Standards Context

According to AWS's official visual update announcement and CloudScape documentation:

- **Color Usage**: Blue is the primary interactive color for buttons, links, tokens, and interactive states. Colors should reinforce brand and user actions while maintaining strong contrast.
- **Typography**: Revised typography scale with improved heading treatment creates stronger visual hierarchy. Labels and keys should be prominent for easier scanning.
- **Visual Hierarchy**: Reduced visual complexity with thinner strokes on containers, unified border styles, and strategic use of shadows only for interactive/transient elements.
- **Information Density**: Optimized spacing with related data displayed closer together, minimized space within containers, and centered wider layouts for modern screen sizes.
- **Consistency**: Distinctive and consistent interface using CloudScape design tokens ensures unified experience across all AWS services.
- **Accessibility**: Color should never be the only visual means of conveying information - pair with iconography or text.

This refactoring will ensure the DRS Orchestration application follows these official AWS design principles.

## Glossary

- **CloudScape**: AWS's open-source design system providing React components and design tokens
- **Design_Token**: Named variables representing design decisions (colors, spacing, typography)
- **Inline_Style**: CSS applied directly via the `style` attribute in JSX
- **CSS_Module**: Scoped CSS file imported into a component
- **Z_Index_Layer**: Stacking context level for overlapping UI elements
- **Theme_Token**: CloudScape design token that adapts to light/dark mode
- **Component**: React component file (.tsx)
- **Frontend_Application**: The React-based UI application in frontend/src/

## Requirements

### Requirement 1: Eliminate Inline Styles

**User Story:** As a developer, I want to remove inline styles from components, so that styles are maintainable and consistent across the application.

#### Acceptance Criteria

1. WHEN reviewing component files, THE Frontend_Application SHALL contain zero inline `style={{}}` attributes except for dynamic values that cannot be predetermined
2. WHEN a component needs custom styling, THE Component SHALL import styles from a dedicated CSS module
3. WHEN dynamic styling is required (e.g., calculated widths, conditional colors), THE Component SHALL use CSS classes with CSS variables rather than inline styles
4. THE Frontend_Application SHALL document all remaining inline styles with justification comments

### Requirement 2: Implement CloudScape Design Tokens

**User Story:** As a developer, I want to use CloudScape design tokens for all styling, so that the UI automatically adapts to theme changes and follows AWS design standards.

#### Acceptance Criteria

1. WHEN defining colors, THE Frontend_Application SHALL use CloudScape color tokens (e.g., `awsui-color-text-body-default`) instead of hardcoded hex values
2. WHEN defining spacing, THE Frontend_Application SHALL use CloudScape spacing tokens (e.g., `awsui-space-scaled-m`) instead of hardcoded pixel values
3. WHEN defining typography, THE Frontend_Application SHALL use CloudScape typography tokens (e.g., `awsui-font-size-body-m`) instead of hardcoded font sizes
4. THE Frontend_Application SHALL replace all instances of hardcoded colors (#5f6b7a, #d13212, #ffffff, etc.) with appropriate CloudScape tokens
5. THE Frontend_Application SHALL replace all hardcoded spacing values (8px, 16px, etc.) with CloudScape spacing scale

### Requirement 3: Create Organized CSS Module Structure

**User Story:** As a developer, I want component-specific styles organized in CSS modules, so that styles are scoped, maintainable, and easy to locate.

#### Acceptance Criteria

1. WHEN a component requires custom styles, THE Frontend_Application SHALL create a corresponding CSS module file (e.g., `ComponentName.module.css`)
2. WHEN organizing CSS modules, THE Frontend_Application SHALL place them adjacent to their component files
3. WHEN multiple components share styles, THE Frontend_Application SHALL create shared CSS modules in `frontend/src/styles/`
4. THE Frontend_Application SHALL use CSS module naming convention with camelCase class names
5. THE Frontend_Application SHALL import CSS modules using TypeScript-safe imports

### Requirement 4: Establish Z-Index Layering System

**User Story:** As a developer, I want a documented z-index layering system, so that overlapping UI elements stack correctly and predictably.

#### Acceptance Criteria

1. THE Frontend_Application SHALL define a centralized z-index scale in `frontend/src/styles/z-index.css`
2. THE Z_Index_Layer system SHALL define layers for: base content (0), dropdowns (1000), modals (2000), modal overlays (1999), tooltips (3000), notifications (4000)
3. WHEN a component needs z-index, THE Component SHALL use CSS custom properties from the centralized z-index scale
4. THE Frontend_Application SHALL document the z-index layering system with usage guidelines
5. THE Frontend_Application SHALL eliminate all hardcoded z-index values from components

### Requirement 5: Refactor Global Styles

**User Story:** As a developer, I want global styles to use CloudScape tokens, so that the application maintains visual consistency with AWS design standards.

#### Acceptance Criteria

1. WHEN defining global styles in `index.css`, THE Frontend_Application SHALL use CloudScape design tokens for colors and spacing
2. THE Frontend_Application SHALL replace hardcoded background color (#f2f3f3) with CloudScape background token
3. THE Frontend_Application SHALL replace hardcoded text color (#16191f) with CloudScape text token
4. THE Frontend_Application SHALL replace hardcoded scrollbar colors with CloudScape color tokens
5. THE Frontend_Application SHALL minimize global styles to only essential resets and base styles

### Requirement 6: Create Design Token Reference

**User Story:** As a developer, I want a comprehensive design token reference, so that I can quickly find the correct token for any styling need.

#### Acceptance Criteria

1. THE Frontend_Application SHALL create a design token reference document in `frontend/src/styles/design-tokens.md`
2. THE design token reference SHALL document commonly used color tokens with examples
3. THE design token reference SHALL document the spacing scale with pixel equivalents
4. THE design token reference SHALL document typography tokens with usage guidelines
5. THE design token reference SHALL include links to official CloudScape documentation

### Requirement 7: Preserve Visual Consistency

**User Story:** As a user, I want the UI to look identical after refactoring, so that my workflow is not disrupted.

#### Acceptance Criteria

1. WHEN comparing before and after screenshots, THE Frontend_Application SHALL maintain identical visual appearance
2. WHEN testing theme switching, THE Frontend_Application SHALL correctly adapt all refactored styles to light/dark mode
3. WHEN testing responsive layouts, THE Frontend_Application SHALL maintain identical breakpoint behavior
4. THE Frontend_Application SHALL pass visual regression tests for all major pages
5. THE Frontend_Application SHALL maintain all existing animations and transitions

### Requirement 8: Implement Migration Strategy

**User Story:** As a developer, I want a phased migration approach, so that refactoring can be done incrementally without breaking the application.

#### Acceptance Criteria

1. THE Frontend_Application SHALL refactor components in priority order: pages first, then shared components, then utilities
2. WHEN refactoring a component, THE Frontend_Application SHALL test it in isolation before integration
3. THE Frontend_Application SHALL maintain a migration checklist tracking refactored components
4. THE Frontend_Application SHALL allow old and new styles to coexist during migration
5. THE Frontend_Application SHALL complete migration in phases with testing between each phase

### Requirement 9: Update Component Examples

**User Story:** As a developer, I want updated component examples, so that I can follow best practices when creating new components.

#### Acceptance Criteria

1. THE Frontend_Application SHALL create example components demonstrating proper CSS module usage
2. THE Frontend_Application SHALL create example components demonstrating CloudScape token usage
3. THE Frontend_Application SHALL document common styling patterns (cards, lists, forms, modals)
4. THE Frontend_Application SHALL provide before/after examples of refactored components
5. THE Frontend_Application SHALL include examples in developer documentation

### Requirement 10: Establish CSS Linting Rules

**User Story:** As a developer, I want CSS linting rules, so that new code follows the established patterns and prevents regression.

#### Acceptance Criteria

1. THE Frontend_Application SHALL configure ESLint to detect inline styles in components
2. THE Frontend_Application SHALL configure Stylelint to enforce CloudScape token usage
3. THE Frontend_Application SHALL configure linting to detect hardcoded color values
4. THE Frontend_Application SHALL configure linting to detect hardcoded spacing values
5. THE Frontend_Application SHALL integrate CSS linting into the CI/CD pipeline

### Requirement 11: Ensure AWS Console Design Compliance

**User Story:** As a product owner, I want the application to follow official AWS Management Console design standards, so that users have a familiar and consistent AWS experience.

#### Acceptance Criteria

1. THE Frontend_Application SHALL use blue (#0972d3 or CloudScape equivalent) as the primary interactive color for buttons, links, and interactive states
2. WHEN displaying status information, THE Frontend_Application SHALL use CloudScape status color tokens (success: green, error: red, warning: orange, info: blue)
3. THE Frontend_Application SHALL use CloudScape typography tokens to maintain AWS console typography scale and hierarchy
4. THE Frontend_Application SHALL use thin borders (1px) on containers and cards, reserving shadows only for interactive and transient elements
5. THE Frontend_Application SHALL optimize information density by using CloudScape spacing tokens that group related data closer together
6. WHEN conveying information with color, THE Frontend_Application SHALL also provide iconography or text alternatives for accessibility
7. THE Frontend_Application SHALL use rounded corners (border-radius) consistent with CloudScape component styling
8. THE Frontend_Application SHALL maintain visual consistency with AWS Management Console by using only CloudScape-approved colors and design patterns

### Requirement 12: Maintain Naming Convention Consistency

**User Story:** As a developer, I want consistent camelCase naming throughout the frontend codebase, so that the application maintains its established coding standards.

#### Acceptance Criteria

1. THE Frontend_Application SHALL use camelCase for all CSS class names in CSS modules
2. THE Frontend_Application SHALL use camelCase for all CSS custom properties (CSS variables)
3. THE Frontend_Application SHALL transform PascalCase data from AWS Service APIs to camelCase at the API boundary
4. THE Frontend_Application SHALL maintain camelCase naming for all JavaScript/TypeScript variables, functions, and properties
5. THE Frontend_Application SHALL document the naming convention transformation pattern in developer documentation

### Requirement 13: Avoid Overriding CloudScape Component Styles

**User Story:** As a developer, I want to avoid overriding CloudScape component internal styles, so that the application remains compatible with CloudScape updates and maintains design system integrity.

#### Acceptance Criteria

1. THE Frontend_Application SHALL NOT add className props to CloudScape components (deprecated by CloudScape)
2. THE Frontend_Application SHALL NOT override CloudScape component internal styles with custom CSS
3. THE Frontend_Application SHALL NOT use !important to override CloudScape styles
4. THE Frontend_Application SHALL NOT target CloudScape internal class names in custom CSS
5. WHEN custom styling is needed around CloudScape components, THE Frontend_Application SHALL wrap components in styled divs
6. WHEN styling variations are needed, THE Frontend_Application SHALL use CloudScape component variant props (e.g., variant="primary")
7. THE Frontend_Application SHALL use CloudScape spacing components (SpaceBetween, Box) for layout instead of custom CSS

### Requirement 14: Support Bidirectional Text (RTL/LTR)

**User Story:** As a developer, I want the application to support bidirectional text, so that it can be used in right-to-left languages without additional implementation effort.

#### Acceptance Criteria

1. THE Frontend_Application SHALL NOT declare explicit text direction (LTR or RTL) in CSS
2. THE Frontend_Application SHALL allow text direction to be inherited from context
3. THE Frontend_Application SHALL use logical CSS properties (margin-inline-start instead of margin-left) where appropriate
4. THE Frontend_Application SHALL test layout in both LTR and RTL modes
5. THE Frontend_Application SHALL ensure CloudScape components inherit direction correctly
