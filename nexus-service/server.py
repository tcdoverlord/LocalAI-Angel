import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

DATA_ROOT = Path(os.environ.get("NEXUS_DATA_ROOT", "/data")).resolve()
GIT_ROOT = (DATA_ROOT / "git").resolve()
REGISTRY_PATH = (DATA_ROOT / "modules.json").resolve()
HOST = "0.0.0.0"
PORT = int(os.environ.get("NEXUS_PORT", "8877"))

GIT_ROOT.mkdir(parents=True, exist_ok=True)
DATA_ROOT.mkdir(parents=True, exist_ok=True)

DEFAULT_MODULES = []


def now():
    return datetime.now(timezone.utc).isoformat()


def load_registry():
    if not REGISTRY_PATH.exists():
        save_registry(DEFAULT_MODULES)
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_registry(modules):
    REGISTRY_PATH.write_text(json.dumps(modules, indent=2), encoding="utf-8")


def safe_slug(value):
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")
    return value[:80] or "repository"


def parse_repo_url(value):
    value = value.strip()
    match = re.match(r"^https://github\.com/([^/]+)/([^/#]+?)(?:\.git)?/?$", value)
    if not match:
        raise ValueError("Only public GitHub HTTPS repository URLs are supported.")
    owner, repo = match.groups()
    repo = safe_slug(repo)
    return owner, repo, f"{owner}/{repo}", f"https://github.com/{owner}/{repo}.git"


def module_path(module):
    path = (GIT_ROOT / module["folder"]).resolve()
    if GIT_ROOT not in path.parents:
        raise ValueError("Invalid module path.")
    return path


def detect_type(path):
    if (path / "index.html").exists():
        return "HTML/Web"
    if (path / "package.json").exists():
        return "Node.js"
    if list(path.glob("*.py")):
        return "Python"
    if list(path.glob("*.ps1")):
        return "PowerShell"
    if (path / "Dockerfile").exists() or (path / "docker-compose.yml").exists():
        return "Docker"
    return "Files"


def list_files(path):
    results = []
    for item in sorted(path.rglob("*")):
        if item.is_file() and ".git" not in item.parts:
            results.append(item.relative_to(path).as_posix())
            if len(results) >= 500:
                break
    return results


def get_module(module_id):
    return next((item for item in load_registry() if item["id"] == module_id), None)


def module_detail(module):
    path = module_path(module)
    installed = module.get("installed", False) and path.is_dir()
    readme = ""
    files = []
    project_type = "Not installed"
    preview_url = None

    if installed:
        readme_path = path / "README.md"
        if readme_path.exists():
            readme = readme_path.read_text(encoding="utf-8", errors="replace")[:200000]
        files = list_files(path)
        project_type = detect_type(path)
        if project_type == "HTML/Web" and (path / "index.html").exists():
            preview_url = f"/preview/{quote(module['id'])}/index.html"

    return {
        "module": {**module, "installed": installed},
        "readme": readme,
        "files": files,
        "project_type": project_type,
        "preview_url": preview_url,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "AngelNexus/3.0"

    def log_message(self, format, *args):
        print(f"[Nexus] {self.address_string()} - {format % args}")

    def send_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def json(self, payload, status=200):
        data = json.dumps(payload).encode("utf-8")
        self.send_headers(status)
        self.wfile.write(data)

    def body(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_OPTIONS(self):
        self.send_headers(204)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/api/health":
            return self.json({"ok": True, "service": "angel-nexus", "version": "3.0"})

        if path == "/api/modules":
            return self.json({"modules": load_registry()})

        match = re.match(r"^/api/modules/([^/]+)$", path)
        if match:
            module = get_module(unquote(match.group(1)))
            if not module:
                return self.json({"error": "Module not found."}, 404)
            return self.json(module_detail(module))

        match = re.match(r"^/preview/([^/]+)/(.+)$", path)
        if match:
            module = get_module(unquote(match.group(1)))
            if not module or not module.get("installed"):
                return self.json({"error": "Module is not installed."}, 404)
            root = module_path(module)
            target = (root / unquote(match.group(2))).resolve()
            if root not in target.parents and target != root:
                return self.json({"error": "Invalid preview path."}, 400)
            if not target.is_file():
                return self.json({"error": "Preview file not found."}, 404)
            content_type = "text/html; charset=utf-8" if target.suffix.lower() in (".html", ".htm") else "text/plain; charset=utf-8"
            self.send_headers(200, content_type)
            self.wfile.write(target.read_bytes())
            return

        return self.json({"error": "Not found."}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        try:
            payload = self.body()
        except Exception:
            return self.json({"error": "Invalid JSON body."}, 400)

        if path == "/api/modules/add":
            try:
                owner, repo, full_name, clone_url = parse_repo_url(payload.get("repo_url", ""))
            except ValueError as exc:
                return self.json({"error": str(exc)}, 400)

            modules = load_registry()
            existing = next((item for item in modules if item["repo"].lower() == full_name.lower()), None)
            if existing:
                return self.json({"message": "Repository already exists.", "module": existing})

            module = {
                "id": safe_slug(f"{owner}-{repo}").lower(),
                "name": repo.replace("-", " ").replace("_", " ").title(),
                "category": "Custom",
                "repo": full_name,
                "clone_url": clone_url,
                "description": "User-added GitHub repository.",
                "folder": safe_slug(repo),
                "installed": False,
                "installed_path": "",
                "updated_at": now(),
            }
            modules.append(module)
            save_registry(modules)
            return self.json({"message": "Repository added to the registry.", "module": module}, 201)

        if path == "/api/modules/install":
            module = get_module(payload.get("id", ""))
            if not module:
                return self.json({"error": "Module not found."}, 404)

            destination = module_path(module)
            destination.parent.mkdir(parents=True, exist_ok=True)

            try:
                if destination.exists() and (destination / ".git").exists():
                    command = ["git", "-C", str(destination), "pull", "--ff-only"]
                    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
                elif destination.exists():
                    return self.json({"error": "Install folder exists but is not a Git repository. Refusing to overwrite it."}, 409)
                else:
                    command = ["git", "clone", "--depth", "1", module["clone_url"], str(destination)]
                    result = subprocess.run(command, capture_output=True, text=True, timeout=180)

                if result.returncode != 0:
                    return self.json({"error": (result.stderr or result.stdout or "Git operation failed")[-4000:]}, 500)

                modules = load_registry()
                for item in modules:
                    if item["id"] == module["id"]:
                        item["installed"] = True
                        item["installed_path"] = str(destination)
                        item["updated_at"] = now()
                save_registry(modules)
                return self.json({"message": "Repository installed successfully.", "module": get_module(module["id"])})
            except subprocess.TimeoutExpired:
                return self.json({"error": "Git operation timed out."}, 504)

        return self.json({"error": "Not found."}, 404)


if __name__ == "__main__":
    print(f"Angel Nexus service listening on {HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()



