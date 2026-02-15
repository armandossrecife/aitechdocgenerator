import markdown
from xhtml2pdf import pisa
import os

def convert_md_to_pdf(md_content: str, output_path: str):
    """
    Converts Markdown content to PDF and saves it using xhtml2pdf.
    """
    # Convert MD to HTML
    html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
    
    # Add basic styling for the PDF
    styled_html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Helvetica, sans-serif; padding: 20px; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            pre {{ background-color: #f4f4f4; padding: 10px; border: 1px solid #ddd; word-wrap: break-word; white-space: pre-wrap; }}
            code {{ font-family: Courier; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Generate PDF
    with open(output_path, "wb") as result_file:
        pisa_status = pisa.CreatePDF(
            styled_html,                # the HTML to convert
            dest=result_file            # file handle to recieve result
        )

    return output_path
