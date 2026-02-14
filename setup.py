#!/usr/bin/env python3
"""
MCP Server Setup Script
Automates installation and initial setup
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command and handle errors"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {description} - Success!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed!")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Ensure Python 3.8+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        print(f"   Current version: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor} detected")
    return True

def main():
    print("=" * 70)
    print("MCP SERVER SETUP")
    print("=" * 70)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing dependencies"
    ):
        sys.exit(1)
    
    # Run context comparison demo
    print("\n" + "=" * 70)
    print("CONTEXT WINDOW COMPARISON DEMO")
    print("=" * 70)
    run_command(
        f"{sys.executable} context_comparison.py",
        "Running comparison demo"
    )
    
    # Instructions for next steps
    print("\n" + "=" * 70)
    print("✅ SETUP COMPLETE!")
    print("=" * 70)
    print()
    print("📚 Next Steps:")
    print()
    print("1️⃣  Start the MCP server:")
    print(f"   {sys.executable} mcp_server.py")
    print()
    print("2️⃣  In another terminal, run the client example:")
    print(f"   {sys.executable} mcp_client_example.py")
    print()
    print("3️⃣  Access the API docs:")
    print("   http://localhost:8000/docs")
    print()
    print("4️⃣  Read the README for more info:")
    print("   cat README.md")
    print()
    print("=" * 70)
    print()
    print("🚀 Your MCP server is ready to reduce context window bloat!")
    print()

if __name__ == "__main__":
    main()
