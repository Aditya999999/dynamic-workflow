import pytest
import os
import sys
from pathlib import Path

# Ensure backend root is on python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))
os.environ["PERSISTENCE_MODE"] = "memory"
os.environ["AGENT_MODE"] = "mock"
os.environ["DWF_AGENT_REGISTRY_PATH"] = "registry/agents.json"
