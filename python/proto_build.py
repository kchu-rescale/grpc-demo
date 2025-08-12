#!/usr/bin/env python3
"""
Generate Python gRPC code from proto files into the python/ directory.

Usage:
  python -m python.proto_build
or
  python python/proto_build.py

This script compiles proto/*.proto into python/api/.
"""
from pathlib import Path
import sys
import subprocess
import re

ROOT = Path(__file__).resolve().parent.parent
PROTO_DIR = ROOT / "proto"
OUT_DIR = ROOT / "python" / "api"


def run(cmd: list[str]):
    print("$", " ".join(cmd))
    subprocess.check_call(cmd)


def fix_relative_imports(out_dir: Path) -> None:
    """Patch generated *_pb2*.py to use relative imports inside the package.

    Example: `import message_pb2 as message__pb2` -> `from . import message_pb2 as message__pb2`.
    """
    pat = re.compile(r"^import ([_a-zA-Z0-9]+_pb2(?:_grpc)?) as ([_a-zA-Z0-9]+)")
    for py in out_dir.glob("*_pb2*.py"):
        text = py.read_text()
        lines = text.splitlines()
        changed = False
        for i, line in enumerate(lines):
            m = pat.match(line)
            if m:
                mod, alias = m.groups()
                lines[i] = f"from . import {mod} as {alias}"
                changed = True
        if changed:
            new_text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
            py.write_text(new_text)
            print(f"Patched relative imports in {py.name}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    protos = [str(p) for p in PROTO_DIR.glob("*.proto")]
    if not protos:
        print("No .proto files found under", PROTO_DIR)
        return 1

    # Ensure imports resolve relative to proto dir
    cmd = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"-I{PROTO_DIR}",
        f"--python_out={OUT_DIR}",
        f"--grpc_python_out={OUT_DIR}",
        *protos,
    ]
    run(cmd)

    # Ensure package imports work
    (OUT_DIR / "__init__.py").write_text("# api package for generated protobuf modules\n")
    fix_relative_imports(OUT_DIR)

    print("Generated Python files in", OUT_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
