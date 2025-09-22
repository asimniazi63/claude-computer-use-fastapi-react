#!/usr/bin/env python3
"""
Energent AI Diagram Generator
Extracts Mermaid diagrams from README.md and generates images in multiple formats.
"""

import os
import sys
import re
import base64
import urllib.parse
import webbrowser
from pathlib import Path
import subprocess

# ANSI color codes
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_colored(text, color=Colors.NC):
    print(f"{color}{text}{Colors.NC}")

def command_exists(command):
    """Check if a command exists in the system."""
    try:
        subprocess.run([command, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def extract_mermaid_from_readme(readme_path):
    """Extract Mermaid diagram from README.md."""
    print_colored("📄 Extracting Mermaid diagram from README.md...", Colors.YELLOW)
    
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find mermaid code blocks
        pattern = r'```mermaid\n(.*?)\n```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if not matches:
            print_colored("❌ No Mermaid diagram found in README.md", Colors.RED)
            return None
        
        # Take the first (main) diagram
        mermaid_content = matches[0].strip()
        print_colored("✅ Mermaid diagram extracted successfully", Colors.GREEN)
        return mermaid_content
        
    except Exception as e:
        print_colored(f"❌ Error reading README.md: {e}", Colors.RED)
        return None

def save_mermaid_file(content, output_path):
    """Save Mermaid content to .mmd file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print_colored(f"✅ Mermaid file saved: {output_path}", Colors.GREEN)
        return True
    except Exception as e:
        print_colored(f"❌ Error saving Mermaid file: {e}", Colors.RED)
        return False

def generate_with_mermaid_cli(mermaid_file, output_dir, base_name):
    """Generate images using Mermaid CLI."""
    if not command_exists("mmdc"):
        print_colored("⚠️  Mermaid CLI not found. Install with: npm install -g @mermaid-js/mermaid-cli", Colors.YELLOW)
        return False
    
    print_colored("🎯 Generating images with Mermaid CLI...", Colors.YELLOW)
    
    success = True
    formats = [
        (".png", ["-w", "1920", "-h", "1080"]),
        (".svg", []),
        (".pdf", [])
    ]
    
    for ext, extra_args in formats:
        output_file = output_dir / f"{base_name}{ext}"
        cmd = ["mmdc", "-i", str(mermaid_file), "-o", str(output_file), "-b", "white"] + extra_args
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print_colored(f"✅ {ext.upper()} generated: {output_file}", Colors.GREEN)
        except subprocess.CalledProcessError as e:
            print_colored(f"❌ Failed to generate {ext.upper()}: {e}", Colors.RED)
            success = False
    
    return success

def generate_html_preview(mermaid_content, output_dir, base_name):
    """Generate HTML preview file."""
    print_colored("🎭 Generating HTML preview...", Colors.YELLOW)
    
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <title>Energent AI Architecture Diagram</title>
    <script src="https://unpkg.com/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background: white;
        }}
        .mermaid {{
            display: flex;
            justify-content: center;
            margin: 20px 0;
        }}
        h1 {{
            text-align: center;
            color: #333;
        }}
        .instructions {{
            max-width: 800px;
            margin: 20px auto;
            padding: 20px;
            background: #f5f5f5;
            border-radius: 8px;
        }}
    </style>
</head>
<body>
    <h1>Energent AI Architecture</h1>
    <div class="mermaid">
{mermaid_content}
    </div>
    
    <script>
        mermaid.initialize({{ 
            startOnLoad: true,
            theme: 'default',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true
            }}
        }});
    </script>
</body>
</html>"""
    
    html_file = output_dir / f"{base_name}.html"
    try:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_template)
        print_colored(f"✅ HTML preview generated: {html_file}", Colors.GREEN)
        return html_file
    except Exception as e:
        print_colored(f"❌ Error generating HTML: {e}", Colors.RED)
        return None

def print_online_links(mermaid_content, base_name):
    """Print online conversion links to console."""
    print_colored("🌐 Online conversion options:", Colors.YELLOW)
    
    # URL encode for mermaid.ink
    encoded_content = base64.b64encode(mermaid_content.encode('utf-8')).decode('utf-8')
    
    print_colored("  📍 Mermaid Live Editor: https://mermaid.live/", Colors.BLUE)
    print_colored(f"  📍 Direct PNG: https://mermaid.ink/img/{encoded_content}", Colors.BLUE)
    print_colored(f"  📍 Direct SVG: https://mermaid.ink/svg/{encoded_content}", Colors.BLUE)
    print_colored("  📍 Multiple formats: https://kroki.io/", Colors.BLUE)

def open_file_manager(directory):
    """Open file manager to the output directory."""
    try:
        if sys.platform == "linux":
            subprocess.run(["xdg-open", str(directory)], check=True)
        elif sys.platform == "darwin":
            subprocess.run(["open", str(directory)], check=True)
        elif sys.platform == "win32":
            subprocess.run(["explorer", str(directory)], check=True)
        else:
            print_colored(f"📁 Check output directory: {directory}", Colors.BLUE)
    except Exception:
        print_colored(f"📁 Check output directory: {directory}", Colors.BLUE)

def main():
    print_colored("🎨 Energent AI Diagram Generator", Colors.BLUE)
    print("==================================")
    
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    readme_file = project_root / "README.md"
    output_dir = project_root / "docs" / "diagrams"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Base name for output files
    base_name = "energent-architecture"
    
    # Extract Mermaid diagram
    mermaid_content = extract_mermaid_from_readme(readme_file)
    if not mermaid_content:
        sys.exit(1)
    
    # Save Mermaid file
    mermaid_file = output_dir / f"{base_name}.mmd"
    if not save_mermaid_file(mermaid_content, mermaid_file):
        sys.exit(1)
    
    print_colored("🚀 Attempting multiple generation methods...", Colors.BLUE)
    print()
    
    # Method 1: Mermaid CLI
    generate_with_mermaid_cli(mermaid_file, output_dir, base_name)
    print()
    
    # Method 2: HTML Preview
    html_file = generate_html_preview(mermaid_content, output_dir, base_name)
    print()
    
    # Method 3: Online links (printed to console)
    print_online_links(mermaid_content, base_name)
    print()
    
    # Summary
    print_colored("🎉 Diagram generation completed!", Colors.GREEN)
    print_colored(f"📁 Output directory: {output_dir}", Colors.BLUE)
    print()
    
    # List generated files
    print_colored("📋 Generated files:", Colors.YELLOW)
    for file in output_dir.glob(f"{base_name}.*"):
        print(f"  {file.name}")
    print()
    
    # Installation tips
    print_colored("💡 Installation Tips:", Colors.BLUE)
    print("  For Mermaid CLI: npm install -g @mermaid-js/mermaid-cli")
    print("  For better results: Install Chrome/Chromium for CLI rendering")
    print()
    
    # Auto-open HTML if available
    if html_file and html_file.exists():
        try:
            print_colored("🌐 Opening HTML preview in browser...", Colors.YELLOW)
            webbrowser.open(html_file.as_uri())
        except Exception:
            print_colored(f"🌐 Open manually: {html_file}", Colors.YELLOW)
    
    # Open file manager
    open_file_manager(output_dir)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("Usage: python generate-diagram.py")
        print("Generates images from Mermaid diagrams in README.md")
        sys.exit(0)
    
    main()
