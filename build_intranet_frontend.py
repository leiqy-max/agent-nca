import os
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
RELEASE_DIR = PROJECT_ROOT / "release"
DEMO_DIR = RELEASE_DIR / "demo"
AGENT_UI_DIR = DEMO_DIR / "agent-ui"


def copy_tree_contents(src: Path, dest: Path):
    if not src.exists():
        raise FileNotFoundError(f"React dist not found: {src}")
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dest / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def build_demo_package():
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    if DEMO_DIR.exists():
        shutil.rmtree(DEMO_DIR)
    DEMO_DIR.mkdir(parents=True, exist_ok=True)

    copy_tree_contents(FRONTEND_DIST, AGENT_UI_DIR)

    zip_base = RELEASE_DIR / "demo"
    zip_path = RELEASE_DIR / "demo.zip"
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(zip_base), "zip", root_dir=RELEASE_DIR, base_dir="demo")

    print(f"Created {zip_path}")
    print(f"Package layout: demo/agent-ui/index.html and demo/agent-ui/assets/*")
    return zip_path


if __name__ == "__main__":
    build_demo_package()
