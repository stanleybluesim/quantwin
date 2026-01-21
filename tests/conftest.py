import sys
from pathlib import Path
import warnings

# Ensure repo root is on sys.path so `import app` works in CI
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Silence jsonschema RefResolver deprecation warning noise
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r"jsonschema\.RefResolver is deprecated.*",
)
