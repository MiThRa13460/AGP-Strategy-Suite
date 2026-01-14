"""
AGP Strategy Suite - Python Backend Entry Point
"""

import asyncio
import sys
from pathlib import Path

# Add package to path
sys.path.insert(0, str(Path(__file__).parent))

from agp_core.server.websocket_server import AGPServer, main

if __name__ == "__main__":
    print("=" * 50)
    print("  AGP Strategy Suite - Python Backend v0.1.0")
    print("=" * 50)
    print()
    asyncio.run(main())
