#!/usr/bin/env python3
"""
AWS Professional Markdown Template Generator

Creates properly formatted markdown templates that follow AWS Professional Services
standards and convert cleanly to professional Word documents with 6-page front matter.

FEATURES:
---------
- Professional AWS document structure with all required sections
- AWS-compliant notices and disclaimers with current year
- Comprehensive placeholder content with formatting examples
- Proper heading hierarchy and formatting guidelines
- Tab-indented bullet points with bold emphasis
- Code block examples with proper syntax
- Automatic filename generation from document title
- File overwrite protection with user confirmation
- **AUTO-GENERATION**: Automatically creates both markdown template AND Word document
- **SINGLE COMMAND WORKFLOW**: One command produces both editable template and final formatted document

GENERATED TEMPLATE STRUCTURE:
-----------------------------
- Document Title (# Heading 1)
- Document Subtitle (## Heading 2)
- Notices section with AWS disclaimers
- Abstract section with comprehensive overview guidelines
- Introduction section with strategic context guidelines
- Executive Summary (# Heading 1) - triggers professional conversion
- Major content sections with formatting examples
- Conclusion with next steps and success factors
- Appendices with resources and references

REQUIREMENTS:
-------------
- Python 3.6 or higher
- Write permissions in current directory
- No external dependencies required
- UTF-8 encoding support

PERMISSIONS NEEDED:
------------------
- File system write access to current directory
- No special system or network permissions required
- Standard user permissions sufficient

USAGE:
------
python create_aws_markdown_template.py <document_title> [document_subtitle]

Arguments:
  document_title        Title for the document (required)
                        Will be used as # Heading 1 and in filename
  document_subtitle     Subtitle for the document (optional)
                        Will be used as ## Heading 2

EXAMPLES:
---------

Basic template with title only:
    python create_aws_markdown_template.py "AWS Migration Strategy"
    # Creates: aws_migration_strategy.md

Template with title and subtitle:
    python create_aws_markdown_template.py "AWS Migration Strategy" "Technical Implementation Guide"
    # Creates: aws_migration_strategy.md

Complex title with special characters:
    python create_aws_markdown_template.py "VMware-to-AWS Migration: Phase 1 Analysis"
    # Creates: vmware_to_aws_migration_phase_1_analysis.md

Windows usage:
    python create_aws_markdown_template.py "Cloud Architecture Review"
    # Creates: cloud_architecture_review.md

FILENAME GENERATION:
-------------------
- Converts title to lowercase
- Replaces spaces and hyphens with underscores
- Removes special characters (keeps only alphanumeric and underscores)
- Adds .md extension
- Example: "AWS Migration Strategy" → "aws_migration_strategy.md"

TEMPLATE CONTENT:
-----------------
Generated templates include:
- Professional document structure for AWS Professional Services
- AWS-compliant notices with current year copyright
- Comprehensive placeholder content with detailed guidelines
- Executive Summary with single-page length constraints (4-5 paragraphs maximum)
- Formatting examples for all supported markdown elements
- Tab-indented bullet points (not spaces)
- Code block examples with language specification
- Proper heading hierarchy (# for title/Executive Summary, ## for major sections)
- Strategic context guidelines for Abstract and Introduction

OUTPUT FORMAT:
--------------
Standard Markdown (.md) files with UTF-8 encoding that:
- Follow AWS Professional Services formatting standards
- Convert cleanly to professional Word documents
- Include 6-page front matter when converted
- Support all markdown elements (headings, lists, code, tables)
- Use proper AWS branding and formatting

ERROR HANDLING:
---------------
- Missing arguments: Clear usage message with examples
- File exists: User confirmation prompt before overwrite
- Write permission issues: Clear error message with file path
- Invalid characters: Automatic filename sanitization
- Encoding issues: UTF-8 encoding enforced

INTEGRATION:
------------
Works seamlessly with:
- **AUTO-INTEGRATION**: Automatically calls markdown_to_docx_converter.py after template creation
- **SINGLE WORKFLOW**: Creates both markdown template and professional Word document in one command
- **VALIDATION SYSTEM**: Validates existing markdown files against AWS professional standards
- **OFFICIAL AWS LOGO**: Automatically downloads and integrates official AWS "Powered by AWS" logo from d0.awsstatic.com
- **AWS COMPLIANCE**: Uses officially approved logo per AWS Trademark Guidelines from AWS Co-Marketing Tools
- **DUAL FUNCTIONALITY**: Template creation for new documents + validation/conversion for existing documents
- AWS_Documentation_Standards_Master_Guide.md for formatting reference
- Standard markdown editors and processors
- Version control systems (Git, etc.)
- **ERROR HANDLING**: Graceful fallback to manual conversion if auto-generation fails

LIMITATIONS:
------------
- Creates files in current directory only
- Filename length limited by filesystem constraints
- Template content is static (no dynamic customization)
- Requires manual content replacement after generation

TROUBLESHOOTING:
----------------
If template creation fails:
1. Check write permissions in current directory
2. Verify Python version is 3.6 or higher
3. Ensure sufficient disk space available
4. Check for filename conflicts and respond to prompts
5. Verify UTF-8 encoding support

BEST PRACTICES:
---------------
- Use descriptive, professional document titles
- Include subtitles for complex or multi-part documents
- Replace all placeholder content with actual content
- Follow formatting guidelines in generated template
- Validate structure before converting to Word
- Use version control for template and final documents

AUTHOR: AWS Professional Services
VERSION: 2.0
DATE: 2024
"""

import sys
import os
import subprocess
from datetime import datetime

def create_professional_template(title, subtitle=None):
    """Create a professional AWS markdown template"""
    
    # Generate filename from title
    filename = title.lower().replace(' ', '_').replace('-', '_')
    filename = ''.join(c for c in filename if c.isalnum() or c == '_')
    filename = f"{filename}.md"
    
    # Template content
    template = f"""# {title}"""
    
    if subtitle:
        template += f"""
## {subtitle}"""
    
    template += f"""

---

## Notices

This document is provided for informational purposes only. It represents AWS's current product offerings and practices as of the date of issue of this document, which are subject to change without notice. Customers are responsible for making their own independent assessment of the information in this document and any use of AWS's products or services, each of which is provided "as is" without warranty of any kind, whether express or implied. This document does not create any warranties, representations, contractual commitments, conditions or assurances from AWS, its affiliates, suppliers or licensors. The responsibilities and liabilities of AWS to its customers are controlled by AWS agreements, and this document is not part of, nor does it modify, any agreement between AWS and its customers.

© {datetime.now().year} Amazon Web Services, Inc. or its affiliates. All rights reserved.

---

## Abstract

[TECHNICAL OVERVIEW FOR PEERS (150-300 words, active voice, present tense)
Write a concise technical summary using active voice and present tense. Address what this document covers and what methodology you used.

Include:
- Document purpose and technical scope (what you analyze, assess, or implement)
- Methodology or approach you employed (how you conducted the work)
- Key technical deliverables and outcomes (what you deliver)
- Target audience (technical peers, stakeholders, decision-makers)
- Brief summary of technical findings or recommendations (what you discovered)

Writing Style Requirements:
- Use active voice: "This document analyzes..." not "Analysis is provided..."
- Use present tense: "The methodology includes..." not "The methodology will include..."
- Be concise and specific to save readers' time
- Explain acronyms when first introduced: "Amazon Web Services (AWS)"
- Use consistent terminology throughout

Keep tone neutral and factual. Focus on technical accuracy and completeness for readers who need to understand the technical approach and deliverables.]

---

## Introduction

[CONTEXT FOR ALL READERS (2-3 paragraphs, direct address using "you")
Provide strategic context and background using direct address to help you understand why this document exists and what problem it addresses.

Include:
- Business or technical challenge you face or need to address
- Current state assessment and key requirements you must consider
- Strategic importance and organizational impact for your environment
- Document structure and how you can navigate it effectively
- Key stakeholders and their roles in your initiative
- Success criteria and expected outcomes you should achieve

Writing Style Requirements:
- Address the reader directly as "you" throughout
- Use imperative mood for instructions: "Follow these steps..." "Consider these factors..."
- Be concise and specific to save your time
- Avoid jargon and explain technical terms clearly
- Use consistent terminology throughout the document

Use an engaging tone that draws you in and helps you understand the broader context and significance of the work described in this document.]

---

# Executive Summary

[BUSINESS CASE FOR DECISION-MAKERS (single page or less, persuasive tone)
Write a concise business case that enables decision-makers to understand the value proposition and make informed decisions about the initiative.

CRITICAL RULES:
- Keep to ONE PAGE OR LESS when converted to Word
- MAXIMUM 4-5 paragraphs total to prevent multi-page issues
- Use bold formatting for key points rather than lengthy subsections
- DO NOT create multiple subsections (##) within Executive Summary
- DO NOT include specific financial predictions, ROI percentages, or assumed cost savings
- DO NOT make quantified claims that can be challenged
- Focus on qualitative benefits and strategic value
- Avoid specific dollar amounts or percentage improvements

Include:
- Strategic business overview and value proposition
- Key findings and recommendations (qualitative benefits)
- Implementation approach and timeline
- Risk mitigation strategies (without financial claims)
- Expected operational benefits and improvements
- Critical decisions needed and recommended actions

Use a persuasive tone that clearly articulates business value through operational improvements, risk reduction, and strategic positioning rather than financial predictions. This section should stand alone as a complete business case.

FORMAT EXAMPLE:
This [document type] establishes [brief overview]. The framework addresses [key challenges].

**Key Business Value:** [Concise value proposition with bold formatting for emphasis]

**Operational Benefits:** [Brief benefits summary with bold formatting]

**Implementation Success:** [Brief implementation approach with bold formatting]

This framework positions [organization outcome statement].]

**Key Features:**
	- [Feature 1]: [Brief description]
	- [Feature 2]: [Brief description]
	- [Feature 3]: [Brief description]

**Key Deliverables:**
	- [Deliverable 1]: [Brief description]
	- [Deliverable 2]: [Brief description]
	- [Deliverable 3]: [Brief description]

---

## [Your First Major Section]

### [Subsection 1]

[Your content here. Use proper formatting:]

**Key Points:**
	- **Important Item**: Description with bold emphasis
	- **Another Item**: Use tab indentation for nested bullets
		- Sub-item with proper indentation
		- Another sub-item
	- **Final Item**: Maintain consistency

### [Subsection 2]

[More content with code examples if needed:]

```python
# Example code block
def example_function():
    \"\"\"
    Properly formatted code with:
    - Consolas font
    - Gray background
    - Proper indentation
    \"\"\"
    return "professional formatting"
```

**Configuration Example:**
```json
{{
  "setting1": "value1",
  "setting2": "value2",
  "nested": {{
    "option": true
  }}
}}
```

---

## [Your Second Major Section]

### [Implementation Steps]

1. **Step 1**: [Description]
	- Detailed sub-step
	- Another sub-step with `inline code`
2. **Step 2**: [Description]
	- Implementation details
	- Best practices
3. **Step 3**: [Description]
	- Validation steps
	- Success criteria

### [Best Practices]

**Recommended Approach:**
	- **Planning Phase**: [Description]
		- Requirements gathering
		- Stakeholder alignment
		- Risk assessment
	- **Implementation Phase**: [Description]
		- Execution strategy
		- Quality assurance
		- Progress monitoring
	- **Validation Phase**: [Description]
		- Testing protocols
		- Performance validation
		- Documentation updates

---

## Conclusion

[Summarize the document including:
- Key takeaways and recommendations
- Next steps and action items
- Success factors and considerations
- Contact information for questions]

**Key Success Factors:**
1. [Factor 1 with detailed explanation]
2. [Factor 2 with detailed explanation]
3. [Factor 3 with detailed explanation]

**Next Steps:**
	- **Immediate Actions**: [Timeline and responsibilities]
	- **Short-term Goals**: [Timeline and responsibilities]
	- **Long-term Objectives**: [Timeline and responsibilities]

---

## Appendices

### Appendix A: [Additional Information]

[Supporting documentation, references, or detailed technical specifications]

### Appendix B: [Resources and References]

**Useful Links:**
	- [AWS Documentation](https://docs.aws.amazon.com/)
	- [AWS Best Practices](https://aws.amazon.com/architecture/well-architected/)
	- [AWS Professional Services](https://aws.amazon.com/professional-services/)

**Internal Resources:**
	- [Internal link 1]
	- [Internal link 2]
	- [Internal link 3]
"""

    return template, filename

def validate_existing_markdown(filename):
    """Validate if existing markdown file follows AWS professional standards"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        headings = [line.strip() for line in lines if line.startswith('#')]
        
        print(f"📋 Validating existing markdown file: {filename}")
        print("=" * 60)
        
        # Check for required professional structure elements
        required_checks = {
            'title': False,
            'subtitle': False,
            'notices': False,
            'abstract': False,
            'introduction': False,
            'executive_summary': False
        }
        
        # Validate structure
        for heading in headings:
            if heading.startswith('# ') and not heading.startswith('# Executive Summary'):
                required_checks['title'] = True
            elif heading.startswith('## ') and 'notices' not in required_checks or not required_checks['notices']:
                if 'notices' in heading.lower():
                    required_checks['notices'] = True
                else:
                    required_checks['subtitle'] = True
            elif heading == '## Abstract':
                required_checks['abstract'] = True
            elif heading == '## Introduction':
                required_checks['introduction'] = True
            elif heading == '# Executive Summary':
                required_checks['executive_summary'] = True
        
        # Check content requirements
        has_aws_copyright = '© 2025 Amazon Web Services, Inc.' in content or '© 2024 Amazon Web Services, Inc.' in content
        has_aws_disclaimer = 'This document is provided for informational purposes only' in content
        
        # Report validation results
        print("🔍 Structure Validation:")
        print(f"  Document Title (# Title):                    {'✓' if required_checks['title'] else '✗'}")
        print(f"  Document Subtitle (## Subtitle):            {'✓' if required_checks['subtitle'] else '✗'}")
        print(f"  Notices Section (## Notices):               {'✓' if required_checks['notices'] else '✗'}")
        print(f"  Abstract Section (## Abstract):             {'✓' if required_checks['abstract'] else '✗'}")
        print(f"  Introduction Section (## Introduction):     {'✓' if required_checks['introduction'] else '✗'}")
        print(f"  Executive Summary (# Executive Summary):    {'✓' if required_checks['executive_summary'] else '✗'}")
        
        print("\n🔍 Content Validation:")
        print(f"  AWS Copyright Notice:                        {'✓' if has_aws_copyright else '✗'}")
        print(f"  AWS Disclaimer Text:                         {'✓' if has_aws_disclaimer else '✗'}")
        
        # Determine if professional document
        is_professional = (required_checks['title'] and required_checks['subtitle'] and 
                          required_checks['notices'] and required_checks['abstract'] and 
                          required_checks['introduction'] and required_checks['executive_summary'] and
                          has_aws_copyright and has_aws_disclaimer)
        
        print(f"\n📊 Overall Assessment:")
        if is_professional:
            print("✅ PASSES: Document follows AWS professional standards")
            print("🎯 Will trigger professional conversion with 6-page front matter")
            return True
        else:
            print("❌ FAILS: Document does not meet AWS professional standards")
            print("💡 Use template generator to create compliant structure")
            return False
            
    except FileNotFoundError:
        print(f"❌ Error: File '{filename}' not found.")
        return False
    except Exception as e:
        print(f"❌ Error validating file: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python create_aws_markdown_template.py <document_title> [document_subtitle]")
        print("   OR: python create_aws_markdown_template.py <existing_markdown_file.md>")
        print("\nExamples:")
        print('  python create_aws_markdown_template.py "AWS Migration Strategy"')
        print('  python create_aws_markdown_template.py "AWS Migration Strategy" "Technical Implementation Guide"')
        print('  python create_aws_markdown_template.py existing_document.md')
        sys.exit(1)
    
    # Check if first argument is an existing .md file
    first_arg = sys.argv[1]
    if first_arg.endswith('.md') and os.path.exists(first_arg):
        print("🔍 Existing markdown file detected - validating AWS compliance...")
        print()
        
        if validate_existing_markdown(first_arg):
            print("\n🔄 Generating Word document from validated markdown...")
            try:
                # Check if converter script exists
                converter_script = "markdown_to_docx_converter.py"
                if os.path.exists(converter_script):
                    # Run the converter
                    result = subprocess.run([
                        sys.executable, converter_script, first_arg
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        # Extract DOCX filename from markdown filename
                        docx_filename = first_arg.replace('.md', '.docx')
                        print(f"✅ Word Document Created Successfully!")
                        print(f"📄 DOCX File: {docx_filename}")
                        print("📋 Professional Features Applied:")
                        print("• 6-page front matter (title, notices, TOC, abstract, introduction)")
                        print("• Official AWS 'Powered by AWS' logo from d0.awsstatic.com (title page & footers)")
                        print("• Page numbering in 'Page X of Y' format starting on page 8")
                        print("• Amazon Ember font throughout document")
                        print("• Amazon orange headings (RGB: 255, 153, 0)")
                        print("• Professional page headers starting on page 8")
                        print("• Clean table formatting and code block styling")
                        print("• AWS Trademark Guidelines compliant branding")
                    else:
                        print(f"⚠️  Word conversion encountered issues:")
                        if result.stderr:
                            print(f"   Error: {result.stderr.strip()}")
                        print(f"   You can manually convert using: python {converter_script} {first_arg}")
                else:
                    print(f"⚠️  Converter script '{converter_script}' not found in current directory")
                    print(f"   Manual conversion: python {converter_script} {first_arg}")
            
            except Exception as e:
                print(f"⚠️  Auto-conversion failed: {e}")
                print(f"   Manual conversion: python markdown_to_docx_converter.py {first_arg}")
        else:
            print("\n💡 To create a compliant template, use:")
            print(f'   python create_aws_markdown_template.py "Your Document Title" "Your Subtitle"')
        
        return
    
    # Original template creation logic
    title = sys.argv[1]
    subtitle = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Create template
    template_content, filename = create_professional_template(title, subtitle)
    
    # Check if file already exists
    if os.path.exists(filename):
        response = input(f"File '{filename}' already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Template creation cancelled.")
            sys.exit(0)
    
    # Write template to file
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        print("✅ AWS Professional Markdown Template Created!")
        print(f"📄 File: {filename}")
        print(f"📝 Title: {title}")
        if subtitle:
            print(f"📝 Subtitle: {subtitle}")
        
        print("\n🎯 Template Features:")
        print("• Professional document structure with title page, notices, TOC, abstract, and introduction")
        print("• Executive Summary section with single-page length guidelines")
        print("• Proper heading hierarchy and formatting guidelines")
        print("• Tab-indented bullet points with bold emphasis")
        print("• Code block examples with proper syntax")
        print("• AWS-compliant notices and disclaimers")
        
        # Auto-generate Word document
        print("\n🔄 Auto-generating Microsoft Word document...")
        try:
            # Check if converter script exists
            converter_script = "markdown_to_docx_converter.py"
            if os.path.exists(converter_script):
                # Run the converter
                result = subprocess.run([
                    sys.executable, converter_script, filename
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Extract DOCX filename from markdown filename
                    docx_filename = filename.replace('.md', '.docx')
                    print(f"✅ Word Document Created Successfully!")
                    print(f"📄 DOCX File: {docx_filename}")
                    print("📋 Professional Features Applied:")
                    print("• 6-page front matter (title, notices, TOC, abstract, introduction)")
                    print("• Official AWS 'Powered by AWS' logo from d0.awsstatic.com (title page & footers)")
                    print("• Page numbering in 'Page X of Y' format starting on page 8")
                    print("• Amazon Ember font throughout document")
                    print("• Amazon orange headings (RGB: 255, 153, 0)")
                    print("• Professional page headers starting on page 8")
                    print("• Clean table formatting and code block styling")
                    print("• AWS Trademark Guidelines compliant branding")
                else:
                    print(f"⚠️  Word conversion encountered issues:")
                    if result.stderr:
                        print(f"   Error: {result.stderr.strip()}")
                    print(f"   You can manually convert using: python {converter_script} {filename}")
            else:
                print(f"⚠️  Converter script '{converter_script}' not found in current directory")
                print(f"   Manual conversion: python {converter_script} {filename}")
        
        except Exception as e:
            print(f"⚠️  Auto-conversion failed: {e}")
            print(f"   Manual conversion: python markdown_to_docx_converter.py {filename}")
        
        print("\n📋 Next Steps:")
        print(f"1. Edit '{filename}' and replace placeholder content with your actual content")
        print("2. Follow the formatting guidelines in the template")
        if os.path.exists(filename.replace('.md', '.docx')):
            print("3. ✅ Word document already created - update as needed after editing markdown")
        else:
            print("3. Re-run converter after editing: python markdown_to_docx_converter.py " + filename)
        
        print("\n🎨 Formatting Guidelines:")
        print("• Use tabs for bullet point indentation (not spaces)")
        print("• Apply **bold formatting** to emphasize key terms")
        print("• Use `inline code` for technical terms and filenames")
        print("• Include code blocks with proper language specification")
        print("• Maintain consistent heading hierarchy")
        
    except Exception as e:
        print(f"❌ Error creating template: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
