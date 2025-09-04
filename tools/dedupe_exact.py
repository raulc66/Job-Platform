
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
candidates = [
    (ROOT / "templates", ROOT / "apps"),
    (ROOT / "static", ROOT / "jobboard" / "static"),  # in case legacy exists
]
def sha(p: Path):
    h = hashlib.sha256()
    with open(p, "rb") as f:
      for chunk in iter(lambda: f.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()

def main():
    removed = 0
    for TPL_ROOT, APPS_ROOT in candidates:
        if not TPL_ROOT.exists() or not APPS_ROOT.exists(): continue
        for app in APPS_ROOT.iterdir():
            tdir = app / "templates"
            if not tdir.is_dir(): continue
            for f in tdir.rglob("*"):
                if not f.is_file(): continue
                rel = f.relative_to(tdir)
                twin = TPL_ROOT / rel
                if twin.exists() and twin.is_file():
                    try:
                        if sha(f) == sha(twin):
                            print("remove dup", f)
                            f.unlink()
                            removed += 1
                    except Exception as e:
                        print("skip", f, e)
    print("removed", removed, "files")
if __name__ == "__main__":
    main()
