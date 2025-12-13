#!/usr/bin/env python3
"""
Unified Confluence Export Script
Complete solution for exporting Confluence pages to Markdown with full automation.

Features:
- Exports pages to Markdown with proper formatting and metadata
- Downloads ALL attachments using REST API (images and files)
- Separates images (images/) and attachments (attachments/) into different directories
- Converts Confluence-specific tags (<ac:image>) to standard HTML before markdown conversion
- Sanitizes filenames: removes Unicode spaces (\u202f), replaces spaces with underscores
- Resolves user mentions (@mentions) to display names with comma separation
- Extracts and formats dates from <time> tags (Month Day, Year format)
- Protects image paths from date formatting to maintain correct links
- Converts Jira datasource tables to static markdown tables with live data
- Converts Confluence task lists to markdown checkboxes
- Includes page metadata: creator, creation date, last editor, last modified date
- Handles escaped placeholders from markdownify
- Comma-separated multi-value fields (sprints, users)
- Recursive export support for entire page trees

Technical Improvements:
- Uses REST API for reliable attachment downloads (no Playwright dependency)
- Handles blob URLs and media IDs correctly
- Markdown-compatible filenames (underscores instead of spaces)
- Proper error handling and progress reporting
"""

import os
import re
import json
import time
import mimetypes
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse, quote, unquote
import requests
from requests.auth import HTTPBasicAuth

from markdownify import markdownify as md
from bs4 import BeautifulSoup

# Configuration
CONFLUENCE_BASE_URL = "https://healthedge.atlassian.net/wiki"
API_BASE = f"{CONFLUENCE_BASE_URL}/rest/api"
EMAIL = "<username>@healthedge.com"
API_TOKEN = "<youyrapitoken>"
ROOT_PAGE_ID = "4805754941"
OUTPUT_DIR = "docs/confluence/markdown"
SESSION_FILE = "confluence_session.json"

class ConfluenceExporter:
    def __init__(self):
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(EMAIL, API_TOKEN)
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })

        
    def get_page(self, page_id: str) -> Dict:
        """Get page content from Confluence API"""
        url = f"{API_BASE}/content/{page_id}"
        params = {
            "expand": "body.storage,space,ancestors,children.page,history,history.lastUpdated,version"
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_child_pages(self, page_id: str) -> List[Dict]:
        """Get all child pages"""
        url = f"{API_BASE}/content/{page_id}/child/page"
        params = {"limit": 100}
        all_children = []
        
        while url:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            all_children.extend(data["results"])
            
            url = None
            if "next" in data.get("_links", {}):
                url = urljoin(API_BASE, data["_links"]["next"])
                params = {}
        
        return all_children
    
    def resolve_user(self, account_id: str) -> str:
        """Resolve user account ID to display name"""
        if not hasattr(self, 'user_cache'):
            self.user_cache = {}
        
        if account_id in self.user_cache:
            return self.user_cache[account_id]
        
        try:
            url = f"{CONFLUENCE_BASE_URL}/rest/api/user"
            params = {'accountId': account_id}
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            user_data = response.json()
            display_name = user_data.get('displayName', f'User-{account_id[:8]}')
            self.user_cache[account_id] = display_name
            return display_name
        except Exception:
            fallback = f"User-{account_id[:8]}"
            self.user_cache[account_id] = fallback
            return fallback
    
    def resolve_users_in_html(self, html: str) -> str:
        """Resolve all user mentions in HTML to display names with commas"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Process each ac:link that contains a user
        for link in soup.find_all('ac:link'):
            user_tag = link.find('ri:user')
            if user_tag:
                account_id = user_tag.get('ri:account-id')
                if account_id:
                    user_name = self.resolve_user(account_id)
                    # Replace link with: name + comma + space
                    link.replace_with(soup.new_string(user_name + ', '))
        
        # Clean up trailing commas and spaces at end of paragraphs
        html_str = str(soup)
        # Remove comma+space before closing tags
        html_str = re.sub(r',\s+</p>', '</p>', html_str)
        html_str = re.sub(r',\s+</td>', '</td>', html_str)
        
        return html_str
    
    def fetch_jira_issues(self, jql: str, columns: List[str]) -> str:
        """Fetch actual Jira issues and create markdown table"""
        try:
            # Query Jira API v3 (new endpoint)
            jira_api_url = "https://healthedge.atlassian.net/rest/api/3/search/jql"
            params = {
                'jql': jql,
                'maxResults': 100,
                'fields': 'issuetype,key,summary,assignee,priority,status,updated,customfield_10020'
            }
            
            response = self.session.get(jira_api_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            issues = data.get('issues', [])
            if not issues:
                return "\n*No issues found matching the query.*\n"
            
            # Column mapping
            column_names = {
                'issuetype': 'Type',
                'key': 'Key',
                'summary': 'Summary',
                'assignee': 'Assignee',
                'priority': 'Priority',
                'status': 'Status',
                'updated': 'Updated',
                'customfield_10020': 'Sprint'
            }
            
            # Build markdown table
            headers = [column_names.get(col, col) for col in columns]
            table = "| " + " | ".join(headers) + " |\n"
            table += "|" + "|".join(["---"] * len(headers)) + "|\n"
            
            for issue in issues:
                fields = issue.get('fields', {})
                row = []
                
                for col in columns:
                    if col == 'issuetype':
                        row.append(fields.get('issuetype', {}).get('name', ''))
                    elif col == 'key':
                        row.append(issue.get('key', ''))
                    elif col == 'summary':
                        row.append(fields.get('summary', ''))
                    elif col == 'assignee':
                        assignee = fields.get('assignee')
                        row.append(assignee.get('displayName', '') if assignee else '')
                    elif col == 'priority':
                        priority = fields.get('priority')
                        row.append(priority.get('name', '') if priority else '')
                    elif col == 'status':
                        status = fields.get('status')
                        row.append(status.get('name', '') if status else '')
                    elif col == 'updated':
                        updated = fields.get('updated', '')
                        if updated:
                            row.append(updated.split('T')[0])
                        else:
                            row.append('')
                    elif col == 'customfield_10020':
                        sprints = fields.get('customfield_10020', [])
                        if sprints and isinstance(sprints, list):
                            sprint_names = []
                            for sprint in sprints:
                                if isinstance(sprint, str) and 'name=' in sprint:
                                    name_part = sprint.split('name=')[1].split(',')[0]
                                    sprint_names.append(name_part)
                            row.append(', '.join(sprint_names))
                        else:
                            row.append('')
                    else:
                        row.append('')
                
                table += "| " + " | ".join(row) + " |\n"
            
            return f"\n\n{table}\n"
            
        except Exception as e:
            print(f"    ⚠️  Error fetching Jira issues: {e}")
            return "\n*Could not fetch Jira issues. See query link above to view in Jira.*\n"
    
    def extract_task_lists(self, html: str) -> str:
        """Extract Confluence task lists and convert to markdown checkboxes"""
        soup = BeautifulSoup(html, 'html.parser')
        tasks_found = 0
        
        for task_list in soup.find_all('ac:task-list'):
            tasks = task_list.find_all('ac:task')
            markdown_tasks = []
            
            for task in tasks:
                status = task.find('ac:task-status')
                body = task.find('ac:task-body')
                
                if status and body:
                    is_complete = status.get_text(strip=True) == 'complete'
                    checkbox = '[x]' if is_complete else '[ ]'
                    task_text = body.get_text(strip=True)
                    markdown_tasks.append(f"- {checkbox} {task_text}")
                    tasks_found += 1
            
            if markdown_tasks:
                markdown_list = '\n'.join(markdown_tasks)
                new_element = soup.new_tag('div')
                new_element.string = f"__TASKLIST_{len(markdown_tasks)}__"
                
                if not hasattr(self, 'task_lists'):
                    self.task_lists = {}
                self.task_lists[f"__TASKLIST_{len(markdown_tasks)}__"] = f"\n\n{markdown_list}\n\n"
                
                task_list.replace_with(new_element)
        
        return str(soup)
    
    def extract_jira_datasources(self, html: str) -> str:
        """Extract Jira datasource tables and fetch real data"""
        soup = BeautifulSoup(html, 'html.parser')
        jira_tables_found = 0
        
        for link in soup.find_all('a', {'data-datasource': True}):
            try:
                datasource_json = link.get('data-datasource', '')
                if not datasource_json:
                    continue
                
                datasource = json.loads(datasource_json)
                jql = datasource.get('parameters', {}).get('jql', '')
                if not jql:
                    continue
                
                views = datasource.get('views', [])
                columns = []
                if views and len(views) > 0:
                    view_props = views[0].get('properties', {})
                    column_data = view_props.get('columns', [])
                    columns = [col.get('key', 'unknown') for col in column_data]
                
                jira_url = link.get('href', '')
                jira_table = self.fetch_jira_issues(jql, columns)
                
                markdown_doc = f"\n\n## Jira Issues Table\n\n"
                markdown_doc += f"**Query:** `{jql}`\n\n"
                markdown_doc += f"**View in Jira:** [{jira_url}]({jira_url})\n"
                markdown_doc += jira_table
                markdown_doc += f"\n*Snapshot taken: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}*\n\n"
                
                new_element = soup.new_tag('div')
                new_element.string = f"__JIRA_TABLE_{jira_tables_found}__"
                
                if not hasattr(self, 'jira_tables'):
                    self.jira_tables = {}
                self.jira_tables[f"__JIRA_TABLE_{jira_tables_found}__"] = markdown_doc
                
                link.replace_with(new_element)
                jira_tables_found += 1
                
            except (json.JSONDecodeError, Exception):
                continue
        
        return str(soup)
    
    def preserve_complex_tables(self, html: str) -> str:
        """Preserve complex tables with rowspan/colspan as cleaned HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        if not hasattr(self, 'preserved_tables'):
            self.preserved_tables = {}
        
        table_count = 0
        for table in soup.find_all('table'):
            # Check if table has rowspan or colspan (complex table)
            has_rowspan = table.find(attrs={'rowspan': True}) is not None
            has_colspan = table.find(attrs={'colspan': True}) is not None
            
            if has_rowspan or has_colspan:
                # Clean up the table HTML - remove Confluence-specific attributes
                for tag in table.find_all(True):
                    # Remove Confluence-specific attributes
                    attrs_to_remove = ['ac:local-id', 'data-layout', 'data-table-width', 
                                     'data-highlight-colour', 'style']
                    for attr in attrs_to_remove:
                        if attr in tag.attrs:
                            del tag.attrs[attr]
                
                # Remove colgroup (column width specifications)
                for colgroup in table.find_all('colgroup'):
                    colgroup.decompose()
                
                # Simplify paragraph tags inside cells
                for p in table.find_all('p'):
                    p.unwrap()
                
                # Get cleaned HTML
                table_html = str(table)
                
                # Add a note and the cleaned table
                note = "\n\n> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].\n\n"
                placeholder = f"__COMPLEX_TABLE_{table_count}__"
                self.preserved_tables[placeholder] = f"{note}{table_html}\n\n"
                
                # Replace table with placeholder
                new_element = soup.new_tag('div')
                new_element.string = placeholder
                table.replace_with(new_element)
                table_count += 1
        
        return str(soup)
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem - removes Unicode spaces and special chars"""
        # Replace Unicode non-breaking spaces with regular spaces first
        filename = filename.replace('\u202f', ' ')
        filename = filename.replace('\u00a0', ' ')
        # Replace all spaces with underscores for markdown compatibility
        filename = filename.replace(' ', '_')
        # Remove other problematic characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Clean up multiple underscores
        filename = re.sub(r'_+', '_', filename)
        filename = filename.strip('._')
        return filename
    
    def convert_confluence_code_blocks(self, html: str) -> str:
        """Convert Confluence code macro to markdown code blocks with placeholders"""
        # Find all code blocks and replace with placeholders
        code_pattern = r'<ac:structured-macro[^>]*ac:name="code"[^>]*>(.*?)</ac:structured-macro>'
        
        def replace_code_block(match):
            full_block = match.group(0)
            
            # Extract language parameter
            lang_match = re.search(r'<ac:parameter ac:name="language">([^<]+)</ac:parameter>', full_block)
            language = lang_match.group(1) if lang_match else ''
            
            # Extract code content from CDATA
            code_match = re.search(r'<!\[CDATA\[(.*?)\]\]>', full_block, re.DOTALL)
            if code_match:
                code_content = code_match.group(1)
                
                # Create a placeholder that will survive markdownify
                placeholder = f"__CODE_BLOCK_{len(self.code_blocks)}__"
                
                # Store the markdown code block
                markdown_code = f"\n```{language}\n{code_content}\n```\n"
                self.code_blocks[placeholder] = markdown_code
                
                return f'<p>{placeholder}</p>'
            
            return full_block
        
        self.code_blocks = {}
        html_with_code_placeholders = re.sub(code_pattern, replace_code_block, html, flags=re.DOTALL)
        return html_with_code_placeholders
    
    def convert_confluence_images_to_html(self, html: str) -> str:
        """Convert Confluence ac:image tags to standard HTML img tags"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all ac:image elements
        for ac_image in soup.find_all('ac:image'):
            # Get the attachment reference
            ri_attachment = ac_image.find('ri:attachment')
            if ri_attachment:
                filename = ri_attachment.get('ri:filename', '')
                if filename:
                    # Sanitize the filename to match what will be saved
                    safe_filename = self.sanitize_filename(filename)
                    
                    # Determine if it's an image based on extension
                    file_ext = Path(safe_filename).suffix.lower()
                    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.bmp', '.tiff'}
                    
                    if file_ext in image_extensions:
                        # Create standard img tag pointing to images directory
                        img_tag = soup.new_tag('img', src=f"images/{safe_filename}", alt=safe_filename)
                        ac_image.replace_with(img_tag)
                    else:
                        # Create link for non-image attachments
                        link_tag = soup.new_tag('a', href=f"attachments/{safe_filename}")
                        link_tag.string = safe_filename
                        ac_image.replace_with(link_tag)
        
        return str(soup)
    
    def save_page_markdown(self, page_data: Dict, parent_path: Path):
        """Save page as markdown with images"""
        title = page_data["title"]
        safe_title = re.sub(r'[<>:"/\\|?*]', '-', title)[:50]
        
        page_dir = parent_path / safe_title
        page_dir.mkdir(parents=True, exist_ok=True)
        images_dir = page_dir / "images"
        images_dir.mkdir(exist_ok=True)
        attachments_dir = page_dir / "attachments"
        attachments_dir.mkdir(exist_ok=True)
        
        # Get page URL
        page_url = f"{CONFLUENCE_BASE_URL}/spaces/{page_data['space']['key']}/pages/{page_data['id']}/{quote(title)}"
        
        # Convert HTML to Markdown with Jira and checkbox processing
        html_content = page_data["body"]["storage"]["value"]
        
        # Convert Confluence code blocks to placeholders first
        html_with_code = self.convert_confluence_code_blocks(html_content)
        
        # Convert Confluence image tags to standard HTML
        html_with_images = self.convert_confluence_images_to_html(html_with_code)
        
        # Resolve user mentions
        html_with_users = self.resolve_users_in_html(html_with_images)
        
        # Extract dates from time tags - use placeholder to preserve through markdownify
        html_with_dates = re.sub(r'<time datetime="([^"]+)"[^>]*/?>', r'<span>__DATE__\1__DATE__</span>', html_with_users)
        
        # Extract and process task lists (checkboxes)
        html_with_tasks = self.extract_task_lists(html_with_dates)
        
        # Extract and process Jira datasources
        html_with_jira = self.extract_jira_datasources(html_with_tasks)
        
        # Preserve complex tables as HTML
        html_with_preserved_tables = self.preserve_complex_tables(html_with_jira)
        
        markdown_content = md(html_with_preserved_tables)
        
        # Restore code blocks - handle escaped underscores
        if hasattr(self, 'code_blocks'):
            for placeholder, code_markdown in self.code_blocks.items():
                # Replace both escaped and unescaped versions
                escaped_placeholder = placeholder.replace('_', r'\_')
                markdown_content = markdown_content.replace(escaped_placeholder, code_markdown)
                markdown_content = markdown_content.replace(placeholder, code_markdown)
        
        # Restore task lists (checkboxes) - handle escaped underscores
        if hasattr(self, 'task_lists'):
            for placeholder, task_markdown in self.task_lists.items():
                # Replace both escaped and unescaped versions
                escaped_placeholder = placeholder.replace('_', r'\_')
                markdown_content = markdown_content.replace(escaped_placeholder, task_markdown)
                markdown_content = markdown_content.replace(placeholder, task_markdown)
        
        # Restore Jira tables - handle escaped underscores
        if hasattr(self, 'jira_tables'):
            for placeholder, jira_doc in self.jira_tables.items():
                # Replace both escaped and unescaped versions
                escaped_placeholder = placeholder.replace('_', r'\_')
                markdown_content = markdown_content.replace(escaped_placeholder, jira_doc)
                markdown_content = markdown_content.replace(placeholder, jira_doc)
        
        # Restore preserved complex tables - handle escaped underscores
        if hasattr(self, 'preserved_tables'):
            for placeholder, table_html in self.preserved_tables.items():
                # Replace both escaped and unescaped versions
                escaped_placeholder = placeholder.replace('_', r'\_')
                markdown_content = markdown_content.replace(escaped_placeholder, table_html)
                markdown_content = markdown_content.replace(placeholder, table_html)
        
        # Remove date placeholders - handle escaped underscores from markdownify
        markdown_content = markdown_content.replace('\\_\\_DATE\\_\\_', '')
        markdown_content = markdown_content.replace('__DATE__', '')
        
        # Format dates from YYYY-MM-DD to Month Day, Year
        # BUT exclude dates in image/link paths (between parentheses or brackets)
        from datetime import datetime
        def format_date(match):
            try:
                # Check if this date is inside a markdown link/image path
                full_text = match.string
                pos = match.start()
                # Look backwards for [ or ( without closing
                check_back = full_text[max(0, pos-100):pos]
                if '(' in check_back or '[' in check_back:
                    # Check if there's a closing before this position
                    last_open_paren = check_back.rfind('(')
                    last_close_paren = check_back.rfind(')')
                    last_open_bracket = check_back.rfind('[')
                    last_close_bracket = check_back.rfind(']')
                    
                    # If we're inside unclosed parentheses or brackets, skip formatting
                    if (last_open_paren > last_close_paren) or (last_open_bracket > last_close_bracket):
                        return match.group(1)
                
                date_obj = datetime.strptime(match.group(1), '%Y-%m-%d')
                return date_obj.strftime('%B %d, %Y')
            except:
                return match.group(1)
        markdown_content = re.sub(r'\b(\d{4}-\d{2}-\d{2})\b', format_date, markdown_content)
        
        # User commas are handled by __USER__ markers in resolve_users_in_html
        # No additional processing needed here
        
        # Note: Markdown references will be updated based on actual file locations
        # Images go to images/, other attachments go to attachments/
        
        # Extract metadata from page data
        from datetime import datetime
        
        # Get creator info
        creator_name = "Unknown"
        created_date = "Unknown"
        if 'history' in page_data and 'createdBy' in page_data['history']:
            creator_name = page_data['history']['createdBy'].get('displayName', 'Unknown')
        if 'history' in page_data and 'createdDate' in page_data['history']:
            try:
                created_dt = datetime.fromisoformat(page_data['history']['createdDate'].replace('Z', '+00:00'))
                created_date = created_dt.strftime('%B %d, %Y')
            except:
                created_date = page_data['history']['createdDate']
        
        # Get last editor info
        last_editor = "Unknown"
        last_modified = "Unknown"
        if 'version' in page_data and 'by' in page_data['version']:
            last_editor = page_data['version']['by'].get('displayName', 'Unknown')
        if 'version' in page_data and 'when' in page_data['version']:
            try:
                modified_dt = datetime.fromisoformat(page_data['version']['when'].replace('Z', '+00:00'))
                last_modified = modified_dt.strftime('%B %d, %Y at %I:%M %p')
            except:
                last_modified = page_data['version']['when']
        
        # Write markdown file
        md_file = page_dir / "README.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(f"**Confluence Page:** {page_url}\n\n")
            f.write(f"**Created by:** {creator_name} on {created_date}  \n")
            f.write(f"**Last modified by:** {last_editor} on {last_modified}\n\n")
            f.write("---\n\n")
            f.write(markdown_content)
        
        print(f"  ✅ Saved: {page_dir}")
        return page_dir, page_url
    

    
    def download_page_attachments(self, page_id: str, images_dir: Path, attachments_dir: Path) -> Tuple[int, int, int]:
        """Download all attachments from a page using API"""
        try:
            # Get attachments from API
            api_url = f"{API_BASE}/content/{page_id}/child/attachment"
            params = {"limit": 500, "expand": "version"}
            
            response = self.session.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
            attachments = data.get('results', [])
            
            if not attachments:
                return 0, 0, 0
            
            downloaded_images = 0
            downloaded_attachments = 0
            skipped = 0
            
            # Image extensions
            image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.bmp', '.tiff'}
            
            for attachment in attachments:
                try:
                    # Get attachment details
                    title = attachment.get('title', 'untitled')
                    download_path = attachment['_links']['download']
                    # Download path already starts with /, so just prepend base URL
                    if download_path.startswith('/'):
                        download_url = f"{CONFLUENCE_BASE_URL}{download_path}"
                    else:
                        download_url = f"{CONFLUENCE_BASE_URL}/{download_path}"
                    
                    # Sanitize filename
                    safe_filename = self.sanitize_filename(title)
                    
                    # Determine if it's an image or other attachment
                    file_ext = Path(safe_filename).suffix.lower()
                    is_image = file_ext in image_extensions
                    
                    # Choose directory
                    target_dir = images_dir if is_image else attachments_dir
                    filepath = target_dir / safe_filename
                    
                    # Skip if already exists
                    if filepath.exists():
                        skipped += 1
                        continue
                    
                    # Download
                    response = self.session.get(download_url, stream=True, timeout=30)
                    response.raise_for_status()
                    
                    # Save file
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    if is_image:
                        downloaded_images += 1
                    else:
                        downloaded_attachments += 1
                    
                except Exception as e:
                    print(f"      ⚠️  Failed to download: {title[:30]} - {str(e)[:50]}")
                    continue
            
            return downloaded_images, downloaded_attachments, skipped
            
        except Exception as e:
            print(f"  ⚠️  Error fetching attachments: {str(e)}")
            return 0, 0, 0
    

    
    def export_page_tree(self, page_id: str, parent_path: Path, indent: int = 0, recursive: bool = True):
        """Export page and optionally children"""
        try:
            page_data = self.get_page(page_id)
            title = page_data["title"]
            print(f"{'  ' * indent}📄 {title}")
            
            # Save page
            page_dir, page_url = self.save_page_markdown(page_data, parent_path)
            
            # Download attachments using API
            images_dir = page_dir / "images"
            attachments_dir = page_dir / "attachments"
            downloaded_images, downloaded_attachments, skipped = self.download_page_attachments(
                page_id, images_dir, attachments_dir
            )
            
            if downloaded_images > 0 or downloaded_attachments > 0 or skipped > 0:
                print(f"{'  ' * indent}  📎 Attachments: {downloaded_images} images, {downloaded_attachments} files, {skipped} skipped")
            
            # Process children only if recursive
            if recursive:
                children = self.get_child_pages(page_id)
                for child in children:
                    self.export_page_tree(child["id"], page_dir, indent + 1, recursive=True)
                
        except Exception as e:
            print(f"{'  ' * indent}❌ Error: {str(e)}")
    
    def generate_index(self):
        """Generate index.md with table of contents"""
        index_file = Path(OUTPUT_DIR) / "index.md"
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write("# Confluence Export - Cloud Migration\n\n")
            f.write("Complete export of Confluence space with pages and images.\n\n")
            f.write("## Table of Contents\n\n")
            
            def write_tree(directory: Path, level: int = 0):
                if not directory.is_dir():
                    return
                
                for item in sorted(directory.iterdir()):
                    if item.name in ['images', 'index.md', '.DS_Store']:
                        continue
                    
                    if item.is_dir():
                        readme = item / "README.md"
                        if readme.exists():
                            title = item.name.replace('-', ' ').title()
                            rel_path = item.relative_to(Path(OUTPUT_DIR))
                            f.write(f"{'  ' * level}- [{title}]({rel_path}/README.md)\n")
                            write_tree(item, level + 1)
            
            write_tree(Path(OUTPUT_DIR))
        
        print(f"\n✅ Generated index: {index_file}")
    
    def run(self):
        """Main export process"""
        print("=" * 60)
        print("🚀 CONFLUENCE COMPLETE EXPORTER")
        print("=" * 60)
        print(f"📂 Output directory: {OUTPUT_DIR}\n")
        
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        
        # Export pages
        self.export_page_tree(ROOT_PAGE_ID, Path(OUTPUT_DIR))
        
        # Generate index
        self.generate_index()
        

        
        print("\n" + "=" * 60)
        print("✅ EXPORT COMPLETE!")
        print("=" * 60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Unified Confluence Exporter with Jira and Checkbox support")
    parser.add_argument('--page-id', help='Confluence page ID to export (default: ROOT_PAGE_ID)')
    parser.add_argument('--output', help='Output directory (default: OUTPUT_DIR)')
    parser.add_argument('--no-recursive', action='store_true', help='Export only specified page')
    
    args = parser.parse_args()
    
    # Override defaults if provided
    if args.page_id:
        ROOT_PAGE_ID = args.page_id
    if args.output:
        OUTPUT_DIR = args.output
    
    exporter = ConfluenceExporter()
    
    if args.page_id:
        # Single page export mode
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        # Respect --no-recursive flag
        recursive = not args.no_recursive
        exporter.export_page_tree(args.page_id, Path(OUTPUT_DIR), indent=0, recursive=recursive)
        print("\n✅ EXPORT COMPLETE!")
    else:
        # Full export mode
        exporter.run()
