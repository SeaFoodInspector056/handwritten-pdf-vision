"""Print portable MCP configuration, or register this installation with Codex."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register-codex", action="store_true")
    args = parser.parse_args()
    server = Path(__file__).resolve().with_name("mcp_server.py")
    config = {"command": sys.executable, "args": ["-B", str(server)]}
    if not args.register_codex:
        print(json.dumps({"mcpServers": {"handwritten-pdf-vision": config}}, indent=2))
        return
    codex = shutil.which("codex")
    if not codex:
        parser.error("Codex CLI was not found. Run without --register-codex for manual configuration.")
    result = subprocess.run([codex, "mcp", "get", "handwritten-pdf-vision", "--json"],
                            capture_output=True, text=True, encoding="utf-8")
    if result.returncode == 0:
        current = json.loads(result.stdout)["transport"]
        if current.get("command") == config["command"] and current.get("args") == config["args"]:
            print("MCP registration already matches this installation.")
            return
        parser.error("A different handwritten-pdf-vision MCP is registered. Review it before replacing it.")
    subprocess.run([codex, "mcp", "add", "handwritten-pdf-vision", "--",
                    config["command"], *config["args"]], check=True)
    print("Registered. Reload the client's MCP connection or restart the app to discover its tools.")


if __name__ == "__main__":
    main()
