#!/usr/bin/env python3
"""
Convert Markdown to PDF using markdown2 and fpdf
"""

import markdown2
import os
from fpdf import FPDF
import re
import sys
import textwrap
import unicodedata

def replace_unicode_chars(text):
    """Replace Unicode characters with ASCII equivalents"""
    # Common replacements
    replacements = {
        '≈': '~',
        '≤': '<=',
        '≥': '>=',
        '—': '-',
        '–': '-',
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
        '…': '...',
        '•': '*',
        '→': '->',
        '←': '<-',
        '↑': '^',
        '↓': 'v',
        '×': 'x',
        '÷': '/',
        '≠': '!=',
        '∞': 'inf',
        '√': 'sqrt',
        '∑': 'sum',
        '∏': 'prod',
        '∫': 'int',
        '∂': 'd',
        '∇': 'nabla',
        '∈': 'in',
        '∉': 'not in',
        '∋': 'ni',
        '∩': 'cap',
        '∪': 'cup',
        '⊂': 'subset',
        '⊃': 'supset',
        '⊆': 'subseteq',
        '⊇': 'supseteq',
        '⊕': 'oplus',
        '⊗': 'otimes',
        '⊥': 'perp',
        '⋅': '.',
        '⌈': 'ceil',
        '⌉': 'ceil',
        '⌊': 'floor',
        '⌋': 'floor',
        '⟨': '<',
        '⟩': '>',
        '⟹': '=>',
        '⟺': '<=>',
    }
    
    # Replace known characters
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    # For other characters, try to normalize or replace with '?'
    result = ""
    for char in text:
        try:
            # Try to encode to latin-1
            char.encode('latin-1')
            result += char
        except UnicodeEncodeError:
            # If it can't be encoded, try to normalize or replace
            normalized = unicodedata.normalize('NFKD', char).encode('ASCII', 'ignore').decode('ASCII')
            result += normalized if normalized else '?'
    
    return result

class PDF(FPDF):
    def __init__(self, title=None):
        super().__init__()
        self.title = title
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        self.set_font("Arial", "B", 16)
        if title:
            self.cell(0, 10, title, 0, 1, "C")
            self.ln(10)
        
    def header(self):
        if self.page_no() > 1:  # Skip header on first page
            self.set_font("Arial", "I", 8)
            self.cell(0, 10, self.title, 0, 0, "L")
            self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "R")
            self.ln(15)
    
    def footer(self):
        if self.page_no() > 1:  # Skip footer on first page
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")
    
    def chapter_title(self, title):
        self.set_font("Arial", "B", 14)
        self.ln(10)
        self.cell(0, 10, replace_unicode_chars(title), 0, 1, "L")
        self.ln(5)
    
    def chapter_body(self, body):
        self.set_font("Arial", "", 11)
        self.multi_cell(0, 10, replace_unicode_chars(body))
        self.ln()
    
    def code_block(self, code, language=None):
        self.set_font("Courier", "", 9)
        self.set_fill_color(240, 240, 240)  # Light gray background
        
        # Wrap code lines to fit page width
        wrapped_lines = []
        for line in code.split('\n'):
            if len(line) > 80:  # Adjust based on your page width
                wrapped_lines.extend(textwrap.wrap(line, width=80))
            else:
                wrapped_lines.append(line)
        
        for line in wrapped_lines:
            self.cell(0, 5, replace_unicode_chars(line), 0, 1, "L", fill=True)
        
        self.set_font("Arial", "", 11)
        self.ln(5)

def convert_markdown_to_pdf(md_file, pdf_file):
    """Convert a Markdown file to PDF"""
    # Read the Markdown file
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Extract title from the first line if it's a heading
    title_match = re.match(r'^#\s+(.+)$', md_content.split('\n')[0])
    title = title_match.group(1) if title_match else os.path.basename(md_file)
    
    # Convert Markdown to HTML
    html_content = markdown2.markdown(
        md_content,
        extras=["fenced-code-blocks", "tables", "header-ids"]
    )
    
    # Create PDF
    pdf = PDF(replace_unicode_chars(title))
    
    # Process the Markdown content
    lines = md_content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Handle headings
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            
            if level == 1:
                pdf.set_font("Arial", "B", 16)
                pdf.ln(10)
                pdf.cell(0, 10, replace_unicode_chars(text), 0, 1, "C")
                pdf.ln(5)
            elif level == 2:
                pdf.set_font("Arial", "B", 14)
                pdf.ln(10)
                pdf.cell(0, 10, replace_unicode_chars(text), 0, 1, "L")
                pdf.ln(5)
            else:
                pdf.set_font("Arial", "B", 12)
                pdf.ln(5)
                pdf.cell(0, 10, replace_unicode_chars(text), 0, 1, "L")
            
            i += 1
            continue
        
        # Handle code blocks
        if line.startswith('```'):
            language = line[3:].strip()
            code_lines = []
            i += 1
            
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1
            
            if i < len(lines):  # Skip the closing ```
                i += 1
            
            pdf.code_block('\n'.join(code_lines), language)
            continue
        
        # Handle paragraphs
        paragraph = []
        while i < len(lines) and lines[i].strip() != '':
            paragraph.append(lines[i])
            i += 1
        
        if paragraph:
            pdf.set_font("Arial", "", 11)
            pdf.multi_cell(0, 10, replace_unicode_chars(' '.join(paragraph)))
            pdf.ln(5)
        
        # Skip empty lines
        while i < len(lines) and lines[i].strip() == '':
            i += 1
    
    # Save the PDF
    pdf.output(pdf_file)
    print(f"PDF saved to {pdf_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python md_to_pdf.py <markdown_file> [pdf_file]")
        sys.exit(1)
    
    md_file = sys.argv[1]
    pdf_file = sys.argv[2] if len(sys.argv) > 2 else md_file.replace('.md', '.pdf')
    
    convert_markdown_to_pdf(md_file, pdf_file)
