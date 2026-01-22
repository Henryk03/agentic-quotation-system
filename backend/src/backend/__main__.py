
import sys
import asyncio

from backend.config import settings


async def async_main():
    print("🔧 Initializing Agentic Backend Server...\n")

    is_valid: bool
    errors: list[str]
    
    is_valid, errors = settings.validate()
    
    if not is_valid:
        print("❌ Configuration errors found:")

        for error in errors:
            print(f"   - {error}")

        print("\n💡 Please edit your .env file to fix these issues.")
        return 1
    
    print(f"✅ Configuration validated.")
    print(f"✅ Configuration loaded from .env\n")

    print(f"🔧 Settings: ")
    print(f"   Host={settings.HOST}")
    print(f"   Port={settings.PORT}")
    print(f"   Headless={settings.HEADLESS}")
    
    print(f"\n🚀 Starting server on {settings.HOST}:{settings.PORT}...")

    from backend.server.websocket_server import start_server
    
    try:
        await start_server(host=settings.HOST, port=settings.PORT)

    except Exception as e:
        print(f"\n❌ Server error: {e}")
        return 1
    
    return 0


def main():
    try:
        return asyncio.run(async_main())
        
    except KeyboardInterrupt:
        print("\n\n👋 Shutdown requested")
        return 0


if __name__ == "__main__":
    sys.exit(main())