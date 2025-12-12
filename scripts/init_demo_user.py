"""
Script to create a demo user for local development and testing
Run with: docker compose exec api python -m scripts.init_demo_user
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.services.auth import AuthService


async def create_demo_user():
    """Create a demo user with safe credentials"""
    DEMO_EMAIL = "demo@example.com"
    DEMO_PASSWORD = "demo123"    
    DEMO_FULL_NAME = "Demo User"

    async with AsyncSessionLocal() as db:
        auth_service = AuthService(db)

        # Check if user already exists
        existing_user = await auth_service.get_user_by_email(DEMO_EMAIL)
        if existing_user:
            print("Demo user already exists!")
            print(f"   Email: {DEMO_EMAIL}")
            print(f"   Password: {DEMO_PASSWORD}")
            print(f"   User ID: {existing_user.id}")
            return

        # Create the user
        try:
            user = await auth_service.create_user(
                email=DEMO_EMAIL,
                password=DEMO_PASSWORD,
                full_name=DEMO_FULL_NAME
            )
            print("Demo user created successfully!")
            print(f"   Email: {user.email}")
            print(f"   Password: {DEMO_PASSWORD}")
            print(f"   User ID: {user.id}")
            print("\nYou can now log in at http://localhost:8000 with these credentials.")

        except Exception as e:
            print("Failed to create demo user!")
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(create_demo_user())