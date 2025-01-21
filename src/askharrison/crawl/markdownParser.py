import re
from collections import defaultdict

import re
from typing import List, Optional, Dict, Any

class Content:
    def __init__(self, id, content_type, content, section_name):
        self.id = id
        self.type = content_type
        self.content = content
        self.section_name = section_name

    def __repr__(self):
        return f"Content {self.id}: {self.type} ({self.content})"

class Section:
    def __init__(self, id, name, level, text=''):
        self.id = id
        self.name = name
        self.level = level
        self.text = text
        self.contents = []  # List of Content objects
        self.previous_section = None
        self.next_section = None
        self.parent_section = None
        self.child_sections = []

    def add_content(self, content):
        self.contents.append(content)

    def print_section(self, base_indent=0, level_diff=1, print_contents=False):
        # Calculate current indentation based on level difference from parent
        current_indent = base_indent + (self.level - level_diff) * 2
        print('  ' * current_indent + f'- {self.name} (Level {self.level})')
        if print_contents:
            for content in self.contents:
                print(' ' * (indent + 2) + f'* {content.type}: {content.content}')
        # Recursively print each child section with increased indentation
        for child in self.child_sections:
            # The level difference for children is their level minus this section's level
            child.print_section(current_indent, self.level)

    def __repr__(self):
        return f"Section {self.id}: {self.name} (Level {self.level})"

    def to_dict(self):
        """convert to dict"""
        return {
            'id': self.id,
            'name': self.name,
            'level': self.level,
            'text': self.text,
            'contents': self.contents,
            'previous_section': self.previous_section,
            'next_section': self.next_section,
            'parent_section': self.parent_section,
            'child_sections': self.child_sections
        }


class MarkdownParser:
    def __init__(self):
        self.sections = []
        self.contents = []
        self.current_section_id = 0
        self.current_content_id = 0

    def parse_markdown_str(self, text: str):
        lines = text.split('\n')
        current_section = None
        code_block_delimiter = False
        table_started = False
        code_block = ''
        table = []

        for line in lines:
            header_match = re.match(r'^(#{1,6})\s*(.*)', line)
            image_match = re.match(r'!\[(.*?)\]\((.*?)\)', line)
            if header_match:
                # End the previous code block or table if it exists
                if code_block_delimiter:
                    self.add_content(current_section, code_block, 'code_block')
                    code_block = ''
                    code_block_delimiter = False
                if table_started:
                    self.add_content(current_section, '\n'.join(table), 'table')
                    table = []
                    table_started = False

                level = len(header_match.group(1))
                name = header_match.group(2).strip()
                current_section = self.add_section(name, level, current_section)
            elif line.startswith('```'):
                if not code_block_delimiter:
                    code_block_delimiter = True
                else:
                    self.add_content(current_section, code_block, 'code_block')
                    code_block = ''
                    code_block_delimiter = False
            elif code_block_delimiter:
                code_block += line + '\n'
            elif image_match:
                image_description = image_match.group(1).strip()
                image_src = image_match.group(2).strip()
                image_content = {
                    'description': image_description,
                    'src': image_src
                }
                self.add_content(current_section, image_content, 'image')
            elif line.startswith('|') and '|' in line[1:]:
                table.append(line)
                table_started = True
            elif table_started and not line.strip():
                # Empty line ends the table
                self.add_content(current_section, '\n'.join(table), 'table')
                table = []
                table_started = False
            elif current_section:
                current_section.text += line + '\n'

        # If a code block or table was the last thing in the document
        if code_block_delimiter:
            self.add_content(current_section, code_block, 'code_block')
        if table_started:
            self.add_content(current_section, '\n'.join(table), 'table')

        self.link_sections()

    def add_section(self, name, level, parent_section):
        section = Section(self.current_section_id, name, level)
        self.current_section_id += 1
        if parent_section and parent_section.level < level:
            section.parent_section = parent_section
            parent_section.child_sections.append(section)
        self.sections.append(section)
        return section

    def add_content(self, section, content, content_type):
        content_obj = Content(self.current_content_id, content_type, content, section.name if section else '')
        self.current_content_id += 1
        self.contents.append(content_obj)
        if section:
            section.add_content(content_obj)

    def link_sections(self):
        for i, section in enumerate(self.sections):
            if i > 0:
                section.previous_section = self.sections[i - 1]
            if i < len(self.sections) - 1:
                section.next_section = self.sections[i + 1]

    def get_hierarchy(self):
        return self.sections

    # def print_hierarchy(self):
    #     for section in self.sections:
    #         print(f"Section {section.id}: {section.name} (Level {section.level})")
    #         for child in section.child_sections:
    #             print(f"  Child Section {child.id}: {child.name}")
    # def print_hierarchy(self):
    #     def print_section(section, indent=''):
    #         print(f"{indent}- {section.name} (Level {section.level})")
    #         for content in section.contents:
    #             print(f"{indent}  * {content.type}: {content.id}")
    #         for child in section.child_sections:
    #             print_section(child, indent + '  '*2)
        
    #     for section in self.sections:
    #         if section.parent_section is None:  # print only top level sections
    #             print_section(section)
    def print_hierarchy(self, print_contents=False):
        # Determine the base level to calculate correct indentation
        base_level = min(section.level for section in self.sections if section.parent_section is None)
        # Start with the top-level sections (which have no parent)
        for section in self.sections:
            if section.parent_section is None:
                section.print_section(level_diff=base_level)


    def get_images(self):
        return [content for content in self.contents if content.type == 'image']

    def get_tables(self):
        return [content for content in self.contents if content.type == 'table']

    def get_code_blocks(self):
        return [content for content in self.contents if content.type == 'code_block']


    def get_section(self, id):
        for section in self.sections:
            if section.id == id:
                return section
        return None

    def get_content(self, id):
        for content in self.contents:
            if content.id == id:
                return content
        return None

class MarkdownParser1:
    def __init__(self, markdown_text):
        self.markdown_text = markdown_text
        self.hierarchy = defaultdict(list)
        self.current_section = 'Root'
        self.parse_text()

    def parse_text(self):
        lines = self.markdown_text.split('\n')
        for line in lines:
            if line.startswith('#'):
                # Determine the level of the header
                level = len(line.split(' ')[0])
                header_text = line[level+1:]
                self.current_section = header_text
                self.hierarchy[level].append(header_text)
            elif line.startswith('!['):
                # Image syntax: ![alt text](URL "Title")
                match = re.match(r'!\[(.*?)\]\((.*?)\s*("(?:.*[^"])")?\s*\)', line)
                if match:
                    alt_text, image_url, title = match.groups()
                    self.hierarchy[self.current_section].append({
                        'type': 'image',
                        'alt_text': alt_text,
                        'url': image_url,
                        'title': title.strip('"') if title else ''
                    })
            elif line.startswith('|') and '|' in line[1:]:
                # Basic table detection
                self.hierarchy[self.current_section].append({'type': 'table', 'content': line})
            elif line.startswith('- ') or line.startswith('* '):
                # Basic list item detection
                self.hierarchy[self.current_section].append({'type': 'list', 'content': line})

    def get_hierarchy(self):
        return self.hierarchy

    def print_hierarchy(self):
        for level, headers in self.hierarchy.items():
            if isinstance(level, int):
                print('Level', level)
                for header in headers:
                    print('  ' * level, header)
            else:
                print(f'Section: {level}')
                for item in headers:
                    if isinstance(item, dict):
                        print('  ' + item['type'] + ':', item.get('content', item.get('url', '')))
                    else:
                        print('  Content:', item)

    def get_tables(self):
        return {section: [item['content'] for item in items if item['type'] == 'table']
                for section, items in self.hierarchy.items() if any(item['type'] == 'table' for item in items)}

    def get_lists(self):
        return {section: [item['content'] for item in items if item['type'] == 'list']
                for section, items in self.hierarchy.items() if any(item['type'] == 'list' for item in items)}

    def get_images(self):
        return {section: [{'url': item['url'], 'alt_text': item['alt_text'], 'title': item['title']} 
                for item in items if item['type'] == 'image']
                for section, items in self.hierarchy.items() if any(item['type'] == 'image' for item in items)}

