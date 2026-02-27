"""
Shared fixtures for deployment architecture tests.

Provides fixtures for loading CloudFormation templates and common test utilities.
"""

import os
import yaml
import pytest
from typing import Dict, Any


# CloudFormation intrinsic function constructors for YAML parsing
def cfn_constructor(loader, tag_suffix, node):
    """Generic constructor for CloudFormation intrinsic functions."""
    if isinstance(node, yaml.ScalarNode):
        return {tag_suffix: loader.construct_scalar(node)}
    elif isinstance(node, yaml.SequenceNode):
        return {tag_suffix: loader.construct_sequence(node)}
    elif isinstance(node, yaml.MappingNode):
        return {tag_suffix: loader.construct_mapping(node)}
    return {tag_suffix: None}


# Register CloudFormation intrinsic function tags
yaml.SafeLoader.add_multi_constructor("!", cfn_constructor)


@pytest.fixture
def cfn_templates_dir():
    """Return the path to the CloudFormation templates directory."""
    return os.path.join(os.path.dirname(__file__), "..", "..", "cfn")


@pytest.fixture
def load_cfn_template():
    """
    Fixture that returns a function to load CloudFormation templates.
    
    Returns:
        Function that takes a relative path and returns parsed YAML template.
    """
    def _load_template(relative_path: str) -> Dict[str, Any]:
        """
        Load a CloudFormation template from the cfn directory.
        
        Args:
            relative_path: Path relative to cfn/ directory (e.g., "iam/roles-stack.yaml")
            
        Returns:
            Parsed CloudFormation template as dictionary
        """
        template_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "cfn",
            relative_path
        )
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        with open(template_path, "r") as f:
            return yaml.safe_load(f)
    
    return _load_template


@pytest.fixture
def load_cfn_template_as_text():
    """
    Fixture that returns a function to load CloudFormation templates as raw text.
    
    Returns:
        Function that takes a relative path and returns template as string.
    """
    def _load_template_text(relative_path: str) -> str:
        """
        Load a CloudFormation template as raw text.
        
        Args:
            relative_path: Path relative to cfn/ directory (e.g., "iam/roles-stack.yaml")
            
        Returns:
            CloudFormation template as raw text string
        """
        template_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "cfn",
            relative_path
        )
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        with open(template_path, "r") as f:
            return f.read()
    
    return _load_template_text


@pytest.fixture
def extract_resource_section():
    """
    Fixture that returns a function to extract a resource section from CloudFormation template text.
    
    Returns:
        Function that takes template text and resource name, returns resource YAML section.
    """
    def _extract_section(template_text: str, resource_name: str) -> str:
        """
        Extract a resource section from CloudFormation template text.
        
        Args:
            template_text: CloudFormation template as string
            resource_name: Name of the resource to extract
            
        Returns:
            YAML section for the specified resource as string, or None if not found
        """
        import re
        
        # Find the resource definition
        pattern = rf"^\s+{re.escape(resource_name)}:\s*$"
        lines = template_text.split("\n")
        
        start_idx = None
        for i, line in enumerate(lines):
            if re.match(pattern, line):
                start_idx = i
                break
        
        if start_idx is None:
            return None
        
        # Find the indentation level of the resource
        resource_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
        
        # Extract lines until we hit another resource at the same level or end
        resource_lines = [lines[start_idx]]
        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            if line.strip() == "":
                resource_lines.append(line)
                continue
            
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= resource_indent and line.strip():
                break
            
            resource_lines.append(line)
        
        return "\n".join(resource_lines)
    
    return _extract_section
