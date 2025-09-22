#!/usr/bin/env python3
"""
Standalone script to start the FastAPI server
This script can be run directly by Docker without module import issues
"""

import os
import sys
import uvicorn

# Add the current directory and computer_use_demo to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'computer_use_demo'))

def main():
    """Main entry point for FastAPI server"""
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8501"))
    
    print(f"🚀 Starting FastAPI server on {host}:{port}")
    print(f"📂 Current working directory: {os.getcwd()}")
    print(f"🐍 Python path: {sys.path}")
    
    # Change to the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📂 Changed working directory to: {os.getcwd()}")
    
    # Test import first
    try:
        print("🧪 Testing FastAPI app import...")
        from computer_use_demo.api.main import app
        print("✅ ✅FastAPI app imported successfully")
    except Exception as e:
        print(f"❌ Failed to import FastAPI app: {e}")
        import traceback
        traceback.print_exc()
        print("🔄 Attempting to run with fallback configuration...")
        
        # Try to run a simple FastAPI app as fallback
        try:
            from fastapi import FastAPI
            fallback_app = FastAPI(title="Computer Use Demo - Fallback Mode")
            
            @fallback_app.get("/")
            async def root():
                return {"message": "Computer Use Demo API - Fallback Mode", "status": "limited"}
            
            @fallback_app.get("/health")
            async def health():
                return {"status": "fallback", "message": "Running in limited mode"}
            
            uvicorn.run(
                fallback_app,
                host=host,
                port=port,
                log_level="info",
                access_log=True,
                reload=False
            )
            return
        except Exception as fallback_error:
            print(f"❌ Fallback mode also failed: {fallback_error}")
            return
    
    try:
        # Run the FastAPI application
        uvicorn.run(
            "computer_use_demo.api.main:app",
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            reload=False
        )
    except Exception as e:
        print(f"❌ Error starting FastAPI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
