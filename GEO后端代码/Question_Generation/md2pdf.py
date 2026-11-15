"""Convert 面试.md to styled HTML, then use Edge to print to PDF."""
import markdown
import subprocess
import os
import time

MD_PATH = r"D:\实习\GEO_Tracker_System\Question_Generation\面试.md"
HTML_PATH = r"D:\实习\GEO_Tracker_System\Question_Generation\面试.html"
PDF_PATH = r"D:\实习\GEO_Tracker_System\Question_Generation\面试.pdf"

with open(MD_PATH, "r", encoding="utf-8") as f:
    md_text = f.read()

html_body = markdown.markdown(
    md_text,
    extensions=["tables", "fenced_code", "codehilite"],
    extension_configs={"codehilite": {"guess_lang": False}},
)

html_full = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
@page {{
    size: A4;
    margin: 2cm 2.2cm;
}}
body {{
    font-family: "Microsoft YaHei", "SimSun", "PingFang SC", sans-serif;
    font-size: 11pt;
    line-height: 1.75;
    color: #1a1a1a;
    max-width: 210mm;
    margin: 0 auto;
    padding: 20px 40px;
}}
h1 {{
    font-size: 20pt;
    text-align: center;
    border-bottom: 2px solid #333;
    padding-bottom: 8px;
    margin-bottom: 16px;
}}
h2 {{
    font-size: 15pt;
    color: #003366;
    border-bottom: 1px solid #ccc;
    padding-bottom: 4px;
    margin-top: 28px;
}}
h3 {{
    font-size: 13pt;
    color: #1a5276;
    margin-top: 20px;
}}
blockquote {{
    border-left: 4px solid #3498db;
    background: #f0f6fb;
    padding: 8px 14px;
    margin: 12px 0;
    color: #2c3e50;
    font-size: 10.5pt;
}}
code {{
    background: #f4f4f4;
    padding: 1px 5px;
    border-radius: 3px;
    font-family: Consolas, "Courier New", monospace;
    font-size: 10pt;
    color: #c7254e;
}}
pre {{
    background: #f8f8f8;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 10px 14px;
    overflow-x: auto;
    font-size: 9.5pt;
    line-height: 1.5;
}}
pre code {{
    background: none;
    padding: 0;
    color: inherit;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
    font-size: 10.5pt;
}}
th, td {{
    border: 1px solid #bbb;
    padding: 6px 10px;
    text-align: left;
}}
th {{
    background: #e8eef5;
    font-weight: bold;
    color: #1a3c5e;
}}
tr:nth-child(even) {{
    background: #fafafa;
}}
strong {{
    color: #1a3c5e;
}}
hr {{
    border: none;
    border-top: 1px solid #ccc;
    margin: 24px 0;
}}
ol, ul {{
    padding-left: 22px;
}}
li {{
    margin-bottom: 4px;
}}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_full)

print(f"HTML saved to: {HTML_PATH}")

# Find Edge executable
edge_paths = [
    os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
    os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
]

edge_exe = None
for p in edge_paths:
    if os.path.exists(p):
        edge_exe = p
        break

if edge_exe:
    print(f"Found Edge: {edge_exe}")
    # Use Edge headless print-to-pdf
    result = subprocess.run([
        edge_exe,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={PDF_PATH}",
        "--no-margins",
        HTML_PATH,
    ], capture_output=True, text=True, timeout=30)
    if os.path.exists(PDF_PATH):
        print(f"PDF saved to: {PDF_PATH}")
    else:
        print(f"Edge finished but PDF not found. stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
else:
    print("Edge not found. HTML file is ready, you can open it in browser and Ctrl+P to save as PDF.")
    print(f"HTML file: {HTML_PATH}")
