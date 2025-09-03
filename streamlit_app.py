"""
Entry point for Streamlit UI - handles import paths correctly.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import the main UI module
from togaf_agent.ui.main import main

if __name__ == "__main__":
    main()