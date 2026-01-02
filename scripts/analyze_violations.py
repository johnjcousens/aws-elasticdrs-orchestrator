#!/usr/bin/env python3
"""
Violation Analysis Script for Python Coding Standards Implementation

This script analyzes the current flake8 violations and categorizes them by severity
and type to create a prioritized migration plan.

Task 3.1: Analyze Current Codebase
"""

import json
import re
import subprocess
from collections import defaultdict
from typing import Dict, List, Tuple


class ViolationAnalyzer:
    """Analyzes flake8 violations and creates migration plan."""

    def __init__(self):
        self.violations = []
        self.categories = {
            'critical': ['F821', 'F822', 'F823', 'F831', 'E999'],  # Undefined names, syntax errors
            'high': ['F401', 'F841', 'E722', 'E702'],  # Unused imports, bare except
            'medium': ['C901', 'E713', 'W504'],  # Complexity, membership tests
            'low': ['E231', 'E221', 'E222', 'E226', 'F541', 'W291', 'W293'],  # Formatting
        }

    def run_flake8(self) -> List[str]:
        """Run flake8 and return violation lines."""
        try:
            result = subprocess.run(
                ['python', '-m', 'flake8', '--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s'],
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except Exception as e:
            print(f"Error running flake8: {e}")
            return []

    def parse_violations(self, lines: List[str]) -> None:
        """Parse flake8 output into structured violations."""
        pattern = r'^(.+?):(\d+):(\d+): (\w+) (.+)$'

        for line in lines:
            if not line.strip():
                continue
                
            match = re.match(pattern, line)
            if match:
                file_path, line_num, col_num, code, message = match.groups()
                
                self.violations.append({
                    'file': file_path,
                    'line': int(line_num),
                    'column': int(col_num),
                    'code': code,
                    'message': message,
                    'severity': self._get_severity(code),
                    'category': self._get_category(code)
                })
    
    def _get_severity(self, code: str) -> str:
        """Determine severity level for violation code."""
        for severity, codes in self.categories.items():
            if code in codes:
                return severity
        return 'low'  # Default to low severity
    
    def _get_category(self, code: str) -> str:
        """Categorize violation by type."""
        if code.startswith('F'):
            if code in ['F401', 'F841']:
                return 'unused_code'
            elif code in ['F821', 'F822', 'F823']:
                return 'undefined_names'
            elif code == 'F541':
                return 'f_string_issues'
            else:
                return 'pyflakes'
        elif code.startswith('E'):
            if code.startswith('E2'):
                return 'whitespace'
            elif code.startswith('E7'):
                return 'statements'
            else:
                return 'pep8_errors'
        elif code.startswith('W'):
            return 'warnings'
        elif code.startswith('C'):
            return 'complexity'
        else:
            return 'other'
    
    def analyze_by_file(self) -> Dict[str, Dict]:
        """Analyze violations grouped by file."""
        file_analysis = defaultdict(lambda: {
            'total_violations': 0,
            'by_severity': defaultdict(int),
            'by_category': defaultdict(int),
            'violations': []
        })
        
        for violation in self.violations:
            file_path = violation['file']
            file_analysis[file_path]['total_violations'] += 1
            file_analysis[file_path]['by_severity'][violation['severity']] += 1
            file_analysis[file_path]['by_category'][violation['category']] += 1
            file_analysis[file_path]['violations'].append(violation)
        
        return dict(file_analysis)
    
    def analyze_by_type(self) -> Dict[str, int]:
        """Analyze violations by type/code."""
        type_counts = defaultdict(int)
        for violation in self.violations:
            type_counts[violation['code']] += 1
        return dict(type_counts)
    
    def get_priority_files(self) -> List[Tuple[str, int, str]]:
        """Get files prioritized by importance and violation count."""
        file_analysis = self.analyze_by_file()
        
        # Priority weights: Lambda functions > Scripts > Tests
        priority_weights = {
            'lambda/': 100,
            'scripts/': 50,
            'tests/': 10
        }
        
        file_priorities = []
        for file_path, analysis in file_analysis.items():
            # Determine base priority
            base_priority = 1
            for prefix, weight in priority_weights.items():
                if file_path.startswith(prefix):
                    base_priority = weight
                    break
            
            # Adjust by severity
            critical_count = analysis['by_severity']['critical']
            high_count = analysis['by_severity']['high']
            
            # Calculate priority score
            priority_score = (
                base_priority + 
                (critical_count * 50) + 
                (high_count * 20) + 
                analysis['total_violations']
            )
            
            file_priorities.append((file_path, priority_score, self._get_file_type(file_path)))
        
        # Sort by priority score (highest first)
        return sorted(file_priorities, key=lambda x: x[1], reverse=True)
    
    def _get_file_type(self, file_path: str) -> str:
        """Determine file type for migration planning."""
        if file_path.startswith('lambda/'):
            return 'lambda_function'
        elif file_path.startswith('scripts/'):
            return 'script'
        elif file_path.startswith('tests/'):
            return 'test'
        else:
            return 'other'
    
    def generate_migration_plan(self) -> Dict:
        """Generate comprehensive migration plan."""
        file_analysis = self.analyze_by_file()
        type_analysis = self.analyze_by_type()
        priority_files = self.get_priority_files()
        
        # Categorize files by migration approach
        auto_fixable = []
        manual_review = []
        complex_refactor = []
        
        for file_path, analysis in file_analysis.items():
            critical_count = analysis['by_severity']['critical']
            complexity_count = analysis['by_category']['complexity']
            
            if critical_count > 0 or complexity_count > 5:
                complex_refactor.append(file_path)
            elif analysis['by_category']['whitespace'] > analysis['total_violations'] * 0.7:
                auto_fixable.append(file_path)
            else:
                manual_review.append(file_path)
        
        return {
            'summary': {
                'total_violations': len(self.violations),
                'total_files': len(file_analysis),
                'by_severity': {
                    severity: sum(1 for v in self.violations if v['severity'] == severity)
                    for severity in ['critical', 'high', 'medium', 'low']
                },
                'by_category': {
                    category: sum(1 for v in self.violations if v['category'] == category)
                    for category in set(v['category'] for v in self.violations)
                }
            },
            'violation_types': type_analysis,
            'priority_files': priority_files[:20],  # Top 20 priority files
            'migration_categories': {
                'auto_fixable': auto_fixable,
                'manual_review': manual_review,
                'complex_refactor': complex_refactor
            },
            'recommendations': self._generate_recommendations(file_analysis, type_analysis)
        }
    
    def _generate_recommendations(self, file_analysis: Dict, type_analysis: Dict) -> List[str]:
        """Generate specific recommendations for migration."""
        recommendations = []
        
        # Check for common patterns
        if type_analysis.get('F401', 0) > 20:
            recommendations.append(
                "High number of unused imports (F401). Consider using autoflake to remove them automatically."
            )
        
        if type_analysis.get('E231', 0) > 30:
            recommendations.append(
                "Many whitespace issues (E231). These can be auto-fixed with Black formatter."
            )
        
        if type_analysis.get('C901', 0) > 10:
            recommendations.append(
                "Multiple complex functions (C901). Consider refactoring to reduce complexity."
            )
        
        if type_analysis.get('F821', 0) > 0:
            recommendations.append(
                "Undefined names found (F821). These require immediate attention as they may cause runtime errors."
            )
        
        # Lambda-specific recommendations
        lambda_files = [f for f in file_analysis.keys() if f.startswith('lambda/')]
        if lambda_files:
            recommendations.append(
                f"Prioritize fixing {len(lambda_files)} Lambda function files as they are production code."
            )
        
        return recommendations
    
    def save_analysis(self, output_file: str = 'violation_analysis.json') -> None:
        """Save analysis results to JSON file."""
        migration_plan = self.generate_migration_plan()
        
        with open(output_file, 'w') as f:
            json.dump(migration_plan, f, indent=2)
        
        print(f"Analysis saved to {output_file}")
    
    def print_summary(self) -> None:
        """Print analysis summary to console."""
        migration_plan = self.generate_migration_plan()
        summary = migration_plan['summary']
        
        print("\n" + "="*60)
        print("PYTHON CODING STANDARDS - VIOLATION ANALYSIS")
        print("="*60)
        
        print(f"\nTotal Violations: {summary['total_violations']}")
        print(f"Total Files: {summary['total_files']}")
        
        print("\nBy Severity:")
        for severity, count in summary['by_severity'].items():
            print(f"  {severity.capitalize()}: {count}")
        
        print("\nBy Category:")
        for category, count in summary['by_category'].items():
            print(f"  {category.replace('_', ' ').title()}: {count}")
        
        print("\nTop Priority Files:")
        for i, (file_path, score, file_type) in enumerate(migration_plan['priority_files'][:10], 1):
            print(f"  {i:2d}. {file_path} (score: {score}, type: {file_type})")
        
        print("\nMigration Categories:")
        categories = migration_plan['migration_categories']
        print(f"  Auto-fixable: {len(categories['auto_fixable'])} files")
        print(f"  Manual review: {len(categories['manual_review'])} files")
        print(f"  Complex refactor: {len(categories['complex_refactor'])} files")
        
        print("\nRecommendations:")
        for i, rec in enumerate(migration_plan['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        print("\n" + "="*60)


def main():
    """Main function to run violation analysis."""
    analyzer = ViolationAnalyzer()
    
    print("Running flake8 analysis...")
    violation_lines = analyzer.run_flake8()
    
    if not violation_lines or (len(violation_lines) == 1 and not violation_lines[0]):
        print("No violations found!")
        return
    
    print(f"Found {len(violation_lines)} violation lines")
    
    analyzer.parse_violations(violation_lines)
    analyzer.print_summary()
    analyzer.save_analysis()


if __name__ == '__main__':
    main()