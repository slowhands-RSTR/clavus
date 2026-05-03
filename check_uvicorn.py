#!/usr/bin/env python3
"""Check if uvicorn is available."""
try:
    import uvicorn
    print(f"uvicorn {uvicorn.__version__}")
except ImportError:
    print("NOT_INSTALLED")