"""Entry point for backend server"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env"""
    backend_root = Path(__file__).parent.parent.parent
    env_path = backend_root / ".env"
    
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ Environment variables loaded from .env")
    else:
        print("⚠️  .env file not found, using system environment variables")

def validate_config():
    """Validate required configuration"""
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key or api_key == "your_api_key_here":
        print("❌ GOOGLE_API_KEY not configured in .env!")
        print("   Please edit .env and add your API key")
        return False
    
    return True

def print_config():
    """Print current configuration"""
    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("PORT", "8080")
    headless = os.getenv("HEADLESS", "true").lower() == "true"
    
    print(f"🔧 Configuration:")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Headless: {headless}")

async def async_main():
    """Async main entry point"""
    print("🔧 Initializing Agentic Backend Server...")
    
    # Load environment
    load_environment()
    
    # Validate configuration
    if not validate_config():
        return 1
    
    # Get configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    print_config()
    
    # Import and start server
    print(f"\n🚀 Starting server on {host}:{port}...\n")
    from backend.server.websocket_server import start_server
    
    try:
        await start_server(host=host, port=port)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        return 1
    
    return 0

def main():
    """Synchronous entry point that runs async_main"""
    try:
        exit_code = asyncio.run(async_main())
        return exit_code
    except KeyboardInterrupt:
        print("\n\n👋 Shutdown requested")
        return 0

if __name__ == "__main__":
    sys.exit(main())