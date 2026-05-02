"""Quick test: call generate_image() directly, bypassing the MCP layer."""

from pathlib import Path
from server import generate_image

output_dir = Path(__file__).resolve().parent / "test-output"
output_dir.mkdir(exist_ok=True)

print("Generating image...")
filepath = generate_image("a small orange tabby kitten sleeping on a cloud", output_dir)
print(f"Saved: {filepath} ({filepath.stat().st_size} bytes)")
