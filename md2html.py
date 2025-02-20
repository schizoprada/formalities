# ~/formalities/md2html.py
import markdown
from pygments.formatters import HtmlFormatter
import os

# Function to generate the HTML content with custom dark theme CSS
def markdown_to_stylized_html(input_file, output_file):
    # Read the Markdown file
    with open(input_file, "r") as file:
        markdown_content = file.read()

    # Convert Markdown to HTML
    html_content = markdown.markdown(
        markdown_content,
        extensions=["fenced_code", "codehilite"]
    )

    # Dark theme CSS for styling
    dark_theme_css = f"""
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #1e1e1e;
            color: #c9d1d9;
            margin: 0;
            padding: 1em;
            line-height: 1.6;
        }}
        a {{
            color: #58a6ff;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        pre {{
            background-color: #0d1117;
            padding: 1em;
            border-radius: 8px;
            overflow-x: auto;
        }}
        code {{
            font-family: Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace;
            background-color: #161b22;
            color: #c9d1d9;
            padding: 0.2em 0.4em;
            border-radius: 4px;
        }}
        @media (max-width: 600px) {{
            body {{
                padding: 0.5em;
                font-size: 90%;
            }}
            pre {{
                font-size: 85%;
            }}
        }}
    </style>
    """

    # Syntax highlighting CSS from Pygments
    pygments_css = f"<style>{HtmlFormatter().get_style_defs('.codehilite')}</style>"

    # Combine everything into final HTML
    final_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stylized Markdown</title>
        {dark_theme_css}
        {pygments_css}
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Write to output HTML file
    with open(output_file, "w") as file:
        file.write(final_html)

    print(f"HTML file generated: {output_file}")

# Example usage
input_file = os.path.expanduser("~/formalities/BRAINSTORM.md")  # Replace with your Markdown file
output_file = os.path.expanduser("~/formalities/BRAINSTORM.html")  # Replace with your desired output file

# Ensure input file exists
if os.path.exists(input_file):
    markdown_to_stylized_html(input_file, output_file)
else:
    print(f"Input file '{input_file}' not found!")
