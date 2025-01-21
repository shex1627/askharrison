from html.parser import HTMLParser
from urllib.request import urlopen
from bs4 import BeautifulSoup
import re

from askharrison.crawl.utils import parse_table, parse_image

class HTMLContent:
    def __init__(self, id, content_type, content, section_name):
        self.id = id
        self.type = content_type
        self.content = content
        self.section_name = section_name

    def __repr__(self):
        return f'Content: {self.type}, Section: {self.section_name}'

    def __str__(self):
        return f'Content: {self.type}, Section: {self.section_name}'
    

class HTMLSection:
    def __init__(self, id, name, level, text=''):
        self.id = id
        self.name = name
        self.level = level
        self.text = text
        self.contents = []
        self.previous_section = None
        self.next_section = None
        self.parent_section = None
        self.child_sections = []

    def add_content(self, content):
        self.contents.append(content)

    def print_section(self, base_indent=0, level_diff=1, print_contents=True):
        current_indent = base_indent + (self.level - level_diff) * 2
        print(' ' * current_indent + f'- {self.name} (Level {self.level})')
        if print_contents:
            for content in self.contents:
                print(' ' * (current_indent + 2) + f'* {content.type}: {content.content}')
        for child in self.child_sections:
            child.print_section(current_indent, self.level)

    def __repr__(self):
        return f'Section: {self.name} (Level {self.level})'

    def __str__(self):
        return f'Section: {self.name} (Level {self.level})'


class HTMLParserExtended:
    def __init__(self):
        self.sections = []
        self.contents = []
        self.current_section_id = 0
        self.current_content_id = 0
        self.current_section = None

    def add_section(self, name, level, parent_section):
        section = HTMLSection(self.current_section_id, name, level)
        self.current_section_id += 1
        if parent_section and parent_section.level < level:
            section.parent_section = parent_section
            parent_section.child_sections.append(section)
        self.sections.append(section)
        return section

    def add_content(self, section, content, content_type):
        content_obj = HTMLContent(self.current_content_id, content_type, content, section.name if section else '')
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

    def parse_html_str(self, html_text: str):
        self.reset()
        soup = BeautifulSoup(html_text, 'html.parser')
        
        # Assume that each section is under a 'div' with a class 'section'
        for section_element in soup.find_all('section'):
            header = section_element.find(re.compile('^h[1-6]$'))
            if header:
                level = int(header.name[1])
                name = header.get_text(strip=True)
                section = self.add_section(name, level, self.current_section)

                table_figures = section_element.find_all('figure', class_='ltx_table')
                for table_figure in table_figures:
                    table_content = parse_table(str(table_figure))
                    if table_content:
                        self.add_content(section, table_content, 'table')
                
                # Parse all image figures
                image_figures = section_element.find_all('figure', class_='ltx_figure')
                for image_figure in image_figures:
                    image_content = parse_image(str(image_figure))
                    if image_content:
                        self.add_content(section, image_content, 'image')
        
        self.link_sections()

    def print_hierarchy(self, print_contents=True):
        base_level = min(section.level for section in self.sections if section.parent_section is None)
        for section in self.sections:
            if section.parent_section is None:
                section.print_section(level_diff=base_level, print_contents=print_contents)

    def get_tables(self):
        return [content for content in self.contents if content.type == 'table']

    def get_images(self):
        return [content for content in self.contents if content.type == 'image']

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

    def reset(self):
        """reset the parser"""
        self.sections = []
        self.contents = []
        self.current_section_id = 0
        self.current_content_id = 0
        self.current_section = None
    