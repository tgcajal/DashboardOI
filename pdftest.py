import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    KeepTogether,
    PageTemplate,
    Frame,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    text = f"Page {page_num}"
    canvas.drawRightString(7.5 * inch, 0.75 * inch, text)

def create_pdf_report(dataframes, pdf_filename):
    """
    Generate a PDF report from a list of DataFrames.

    Parameters:
    - dataframes: List of tuples in the format (title, DataFrame)
    - pdf_filename: Name of the output PDF file
    """
    # Set up the PDF document
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    elements = []
    styles = getSampleStyleSheet()
    style_heading = styles['Heading1']

    for idx, (title, df) in enumerate(dataframes):
        # Create a list to hold the elements for the current table
        table_elements = []

        # Add a title for each table
        table_title = Paragraph(title, style_heading)
        table_elements.append(table_title)
        table_elements.append(Spacer(1, 12))

        # Convert DataFrame to a list of lists
        data = [df.columns.tolist()] + df.values.tolist()

        # Create the table
        table = Table(data)
        table.hAlign = 'LEFT'  # Align the table to the right

        # Apply styling to the table
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d5dae6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f2f2f2')]),
        ]))

        table_elements.append(table)
        table_elements.append(Spacer(1, 24))

        # Wrap the table elements in KeepTogether to prevent splitting
        elements.append(KeepTogether(table_elements))

    # Add page numbers
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    template = PageTemplate(id='PageTemplate', frames=frame, onPage=add_page_number)
    doc.addPageTemplates([template])

    # Build the PDF
    doc.build(elements)
    #print(f"PDF report '{pdf_filename}' has been created successfully.")
