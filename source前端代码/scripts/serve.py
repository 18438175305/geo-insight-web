"""Serve the demonstration locally with Python's standard library."""
import argparse
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
args = parser.parse_args()
directory = Path(__file__).resolve().parents[1] / "dist"
handler = partial(SimpleHTTPRequestHandler, directory=str(directory))
print(f"Open http://127.0.0.1:{args.port}", flush=True)
ThreadingHTTPServer(("127.0.0.1", args.port), handler).serve_forever()
