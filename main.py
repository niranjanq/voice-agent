"""Root entry point for Sunrise Clinic Local AI Receptionist."""

import asyncio
from backend.main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
