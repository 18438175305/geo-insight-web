"""Export the hosted entry point as one portable HTML file."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
html = (root / "dist/index.html").read_text(encoding="utf-8")
javascript = (root / "dist/app.js").read_text(encoding="utf-8").replace("</", "<\\/")
output = root / "GEO-Insight.html"
output.write_text(html.replace('<script src="app.js"></script>', "<script>\n" + javascript + "\n</script>"), encoding="utf-8")
print(output)
