import fitz  # PyMuPDF
import pandas as pd
import re

class ArXivPDFParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.document = fitz.open(filepath)
        self.metadata = self.extract_metadata()
        self.content = []
        self.figures = []
        self.tables = []

    def extract_metadata(self):
        # Extracts metadata from the PDF
        metadata = self.document.metadata
        return {
            'title': metadata.get('title', ''),
            'author': metadata.get('author', ''),
            'creationDate': metadata.get('creationDate', ''),
        }
    
    def extract_text(self):
        # Extracts text from each page
        for page in self.document:
            self.content.append(page.get_text())

    def extract_figures(self):
        # Identify and extract figures from the PDF
        for page_num, page in enumerate(self.document, start=1):
            for img in page.get_images(full=True):
                # Store image info and the page it's found on
                self.figures.append({'page': page_num, 'image': img})

    def extract_sections(self):
        # Initialize a dictionary to hold the sections
        sections = {}
        current_section = "Introduction"  # The first section is often the Introduction

        for page in self.document:
            blocks = page.get_text("dict")["blocks"]

            for b in blocks:  # iterate through the text blocks
                if 'lines' in b:  # text blocks only
                    for line in b['lines']:
                        for span in line['spans']:  # check each text span within the line
                            if span['flags'] & 16 or span['size'] > 13:  # heuristic for bold text or font size indicative of a title
                                current_section = span['text'].strip()
                                sections[current_section] = ""
                            else:
                                sections[current_section] += span['text'] + ' '

        # Clean up any space and newline characters
        for section, text in sections.items():
            sections[section] = re.sub('\s+', ' ', text).strip()

        self.sections = sections

    def extract_tables(self):
        # Placeholder for table extraction logic
        for page_num, page in enumerate(self.document, start=1):
            for image in page.get_images(full=True):
                # We assume that tables are also presented as images
                xref = image[0]  # xref is the reference number for the image
                base_image = self.document.extract_image(xref)
                image_bytes = base_image["image"]

                # Here you would have the image bytes of what is likely a table
                # You could use additional image processing to convert this to data
                # For this example, we'll just keep the bytes
                self.tables.append({
                    'page': page_num,
                    'image_bytes': image_bytes,
                    # 'data': ... # Some function to convert image_bytes to data
                })

    def parse(self):
        self.extract_sections()
        #self.extract_tables()

