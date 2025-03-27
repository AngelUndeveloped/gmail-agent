from src.utils.secrets import secrets
from src.auth import get_auth_url
import asyncio

async def test_setup():
    print("Testing Gmail Agent Setup...")
    
    # Test secrets
    print("\n1. Testing secrets...")
    try:
        secrets.validate_secrets()
        print("✅ Secrets validation passed")
    except ValueError as e:
        print(f"❌ Secrets validation failed: {e}")
        return

    # Test OAuth URL generation
    print("\n2. Testing OAuth URL generation...")
    try:
        auth_url = get_auth_url()
        print("✅ OAuth URL generation successful")
        print(f"Auth URL: {auth_url}")
    except Exception as e:
        print(f"❌ OAuth URL generation failed: {e}")
        return

    print("\n🎉 Setup test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_setup()) 