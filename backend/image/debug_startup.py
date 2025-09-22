#!/usr/bin/env python3
"""
Debug startup script to help identify issues in Docker container
"""

import os
import sys
import subprocess

print("🔍 Debug Information")
print("=" * 50)

print(f"🐍 Python executable: {sys.executable}")
print(f"🐍 Python version: {sys.version}")
print(f"📂 Current working directory: {os.getcwd()}")
print(f"📂 Home directory: {os.environ.get('HOME', 'N/A')}")
print(f"📂 Python path: {sys.path}")

print("\n📦 Checking installed packages...")
try:
    import fastapi
    print(f"✅ FastAPI version: {fastapi.__version__}")
except ImportError:
    print("❌ FastAPI not installed")

try:
    import uvicorn
    print(f"✅ Uvicorn available")
except ImportError:
    print("❌ Uvicorn not installed")

try:
    import anthropic
    print(f"✅ Anthropic available")
except ImportError:
    print("❌ Anthropic not installed")

print("\n📁 Directory structure:")
for root, dirs, files in os.walk("/home/computeruse"):
    level = root.replace("/home/computeruse", "").count(os.sep)
    indent = " " * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    sub_indent = " " * 2 * (level + 1)
    for file in files[:10]:  # Limit to first 10 files
        print(f"{sub_indent}{file}")
    if len(files) > 10:
        print(f"{sub_indent}... and {len(files) - 10} more files")

print("\n🔍 Environment variables:")
for key in ["ANTHROPIC_API_KEY", "DISPLAY", "DISPLAY_NUM", "WIDTH", "HEIGHT"]:
    print(f"{key}: {os.environ.get(key, 'Not set')}")

print("\n🧪 Testing imports...")
try:
    sys.path.insert(0, "/home/computeruse")
    from computer_use_demo.api.main import app
    print("✅ Main app imported successfully")
except Exception as e:
    print(f"❌ Failed to import main app: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("🏁 Debug complete!")
