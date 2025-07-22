#!/usr/bin/env python3
"""
Demo script to showcase CLI tool integration
"""

import json
from pathlib import Path

def main():
    print("🚀 Gary-Zero CLI Tools Integration Demo")
    print("=" * 50)
    
    # Show the new files created
    print("\n📁 New Files Created:")
    
    new_files = [
        "framework/tools/openai_codex_cli.py",
        "framework/tools/google_gemini_cli.py",
        "instruments/default/openai_codex/README.md",
        "instruments/default/openai_codex/install.sh",
        "instruments/default/google_gemini/README.md", 
        "instruments/default/google_gemini/install.sh",
        "prompts/default/fw.codex_cli.usage.md",
        "prompts/default/fw.gemini_cli.usage.md"
    ]
    
    for file_path in new_files:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"✅ {file_path} ({size} bytes)")
        else:
            print(f"❌ {file_path} (missing)")
    
    # Show settings integration
    print("\n⚙️ Settings Integration:")
    
    try:
        from framework.helpers.settings.types import DEFAULT_SETTINGS
        
        cli_settings = [k for k in DEFAULT_SETTINGS.keys() if 'cli' in k]
        print(f"✅ CLI settings added: {len(cli_settings)} new settings")
        for setting in cli_settings:
            print(f"   - {setting}: {DEFAULT_SETTINGS[setting]}")
            
    except Exception as e:
        print(f"❌ Settings check failed: {e}")
    
    # Show tool capabilities
    print("\n🛠️ Tool Capabilities:")
    
    print("\n🔧 OpenAI Codex CLI Features:")
    print("   - Context-aware code editing")
    print("   - AI-powered file creation")  
    print("   - Intelligent shell commands")
    print("   - Safety controls and approval modes")
    print("   - Auto-installation support")
    
    print("\n🤖 Google Gemini CLI Features:")
    print("   - Interactive chat with Gemini models")
    print("   - Code generation and analysis")
    print("   - Content generation")
    print("   - Configuration management")
    print("   - Multiple model support")
    
    # Show safety features
    print("\n🔐 Safety Features:")
    print("   - Approval modes: suggest, auto, block")
    print("   - Sandboxed command execution")
    print("   - Timeout controls")
    print("   - Comprehensive error handling")
    print("   - User-controlled auto-installation")
    
    # Show usage examples
    print("\n📚 Usage Examples:")
    
    print("\n📝 Edit a file with Codex CLI:")
    print("   action: edit")
    print("   file_path: /path/to/file.py") 
    print("   instruction: Add error handling to the main function")
    
    print("\n💬 Chat with Gemini:")
    print("   action: chat")
    print("   message: Explain how machine learning works")
    print("   model: gemini-pro")
    
    print("\n🎯 Generate code with Gemini:")
    print("   action: code")
    print("   task: Create a function to sort an array")
    print("   language: python")
    
    print("\n✨ Installation:")
    print("   Both CLIs can be installed automatically or manually:")
    print("   - OpenAI Codex: npm install -g @openai/codex-cli")
    print("   - Google Gemini: pip install google-generativeai[cli]")
    
    print("\n🎉 Integration Complete!")
    print("Gary-Zero now supports both OpenAI Codex CLI and Google Gemini CLI")


if __name__ == "__main__":
    main()