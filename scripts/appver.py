#!/usr/bin/env python3
"""Read and change version / build numbers across project types.

  appver.py show <repo>
  appver.py bump-build <repo> [--only KIND] [--platform P] [--path SUBSTR] [--to N]
  appver.py set-version <repo> X.Y.Z [--only KIND] [--platform P] [--path SUBSTR]

Kinds: xcodegen, xcode, gradle, flutter, expo, npm, tauri, cargo, python,
dotnet, extension, file.

--platform filters Apple targets by SDK (ios, tvos, macos, watchos, visionos);
`android` is an alias for --only gradle.
--path keeps only files whose relative path contains SUBSTR (monorepos).

Build counters: all Apple targets share one counter (max + 1); every other
file increments its own. --to N sets an explicit number instead.
Only the standard library is used; edits are regex-based and keep formatting.
"""
import argparse, json, pathlib, re, sys

# .claude: agent worktrees; dist: exported archives
SKIP_DIRS = {"build", "DerivedData", "Pods", ".git", "node_modules", ".build", ".claude", "dist",
             "vendor", "target", ".venv", "venv", ".dart_tool", "Carthage", "bin", "obj", ".next", "out"}
SDK_TO_PLATFORM = {"iphoneos": "ios", "appletvos": "tvos", "macosx": "macos", "watchos": "watchos", "xros": "visionos"}
APPLE = {"xcode", "xcodegen"}


def walk(root, pattern):
    for p in sorted(root.rglob(pattern)):
        rel = p.relative_to(root).parts
        if not SKIP_DIRS.intersection(rel) and not any(x.endswith(".xcarchive") for x in rel):
            yield p


def sub_once(pattern, repl, text, flags=0):
    new, n = re.subn(pattern, repl, text, count=1, flags=flags)
    return new if n else text


# --- Xcode / XcodeGen -------------------------------------------------------

def xcode_blocks(text):
    """Yield (start, end, info) for each shipping XCBuildConfiguration."""
    for m in re.finditer(r"isa = XCBuildConfiguration;\s*buildSettings = \{(.*?)\n\t\t\t\};", text, re.S):
        body = m.group(1)
        get = lambda k: (re.search(rf"\b{k} = \"?([^\";]+)\"?;", body) or [None, None])[1]
        bundle = get("PRODUCT_BUNDLE_IDENTIFIER")
        if not bundle or re.search(r"tests?$", bundle, re.I):
            continue
        sdk = get("SDKROOT") or ""
        yield m.start(1), m.end(1), {
            "bundle": bundle, "platform": SDK_TO_PLATFORM.get(sdk, sdk or "?"),
            "version": get("MARKETING_VERSION"), "build": get("CURRENT_PROJECT_VERSION"),
        }


def read_xcode(path, text):
    seen = {}
    for _, _, b in xcode_blocks(text):
        if b["version"] or b["build"]:
            seen.setdefault((b["platform"], b["bundle"]), b)
    return [{"label": f"{p} {bundle}", "version": b["version"], "build": b["build"], "platform": p}
            for (p, bundle), b in seen.items()]


def write_xcode(text, version, build, platform):
    out, last = [], 0
    for start, end, b in xcode_blocks(text):
        if platform and b["platform"] != platform:
            continue
        body = text[start:end]
        if version:
            body = re.sub(r"(\bMARKETING_VERSION = )\"?[^\";]+\"?;", rf"\g<1>{version};", body)
        if build is not None and b["build"]:
            body = re.sub(r"(\bCURRENT_PROJECT_VERSION = )\"?[^\";]+\"?;", rf"\g<1>{build};", body)
        out += [text[last:start], body]
        last = end
    return "".join(out) + text[last:]


def read_xcodegen(path, text):
    get = lambda k: sorted(set(re.findall(rf"^\s*{k}:\s*\"?([^\"\n]+?)\"?\s*$", text, re.M)))
    v, b = get("MARKETING_VERSION"), get("CURRENT_PROJECT_VERSION")
    if not (v or b):
        return []
    return [{"label": "XcodeGen spec (run `xcodegen generate` after edits)",
             "version": ", ".join(v) or None, "build": ", ".join(b) or None}]


def write_xcodegen(text, version, build, platform):
    if version:
        text = re.sub(r"^(\s*MARKETING_VERSION:\s*)\"?[^\"\n]+\"?", rf'\g<1>"{version}"', text, flags=re.M)
    if build is not None:
        text = re.sub(r"^(\s*CURRENT_PROJECT_VERSION:\s*)\"?[^\"\n]+\"?", rf'\g<1>"{build}"', text, flags=re.M)
    return text


# --- Android / Flutter / Expo -----------------------------------------------

def read_gradle(path, text):
    code = re.search(r"\bversionCode\s*=?\s*(\d+)", text)
    name = re.search(r"\bversionName\s*=?\s*\"([^\"]+)\"", text)
    if not (code or name):
        return []
    return [{"label": "android", "version": name and name[1], "build": code and code[1]}]


def write_gradle(text, version, build, platform):
    if version:
        text = re.sub(r"(\bversionName\s*=?\s*)\"[^\"]+\"", rf'\g<1>"{version}"', text)
    if build is not None:
        text = re.sub(r"(\bversionCode\s*=?\s*)\d+", rf"\g<1>{build}", text)
    return text


PUBSPEC = r"^(version:\s*)([0-9][^\s+#]*)(?:\+(\d+))?"


def read_flutter(path, text):
    m = re.search(PUBSPEC, text, re.M)
    return [{"label": "pubspec (version+build for iOS and Android)", "version": m[2], "build": m[3]}] if m else []


def write_flutter(text, version, build, platform):
    m = re.search(PUBSPEC, text, re.M)
    v, b = version or m[2], build if build is not None else m[3]
    return text[:m.start()] + f"{m[1]}{v}" + (f"+{b}" if b else "") + text[m.end():]


def read_expo(path, text):
    expo = json.loads(text).get("expo")
    if not isinstance(expo, dict):
        return []
    rows = [{"label": "expo version", "version": expo.get("version"), "build": None}]
    if "buildNumber" in expo.get("ios", {}):
        rows.append({"label": "expo ios.buildNumber", "version": None, "build": expo["ios"]["buildNumber"]})
    if "versionCode" in expo.get("android", {}):
        rows.append({"label": "expo android.versionCode", "version": None, "build": str(expo["android"]["versionCode"])})
    return rows


def write_expo(text, version, build, platform):
    if version:
        text = sub_once(r'("version"\s*:\s*)"[^"]*"', rf'\g<1>"{version}"', text)
    if build is not None:
        text = sub_once(r'("buildNumber"\s*:\s*)"[^"]*"', rf'\g<1>"{build}"', text)
        text = sub_once(r'("versionCode"\s*:\s*)\d+', rf"\g<1>{build}", text)
    return text


# --- JSON manifests (npm, Tauri, browser extensions) -------------------------

def json_version_reader(label, predicate=lambda d: True):
    def read(path, text):
        try:
            data = json.loads(text)
        except ValueError:
            return []
        if not isinstance(data, dict) or "version" not in data or not predicate(data):
            return []
        name = data.get("name") or ""
        return [{"label": f"{label} {name}".strip(), "version": data["version"], "build": None}]
    return read


def write_json_version(text, version, build, platform):
    old = json.loads(text)["version"]
    return sub_once(rf'("version"\s*:\s*)"{re.escape(old)}"', rf'\g<1>"{version}"', text) if version else text


def is_extension(d):
    return "manifest_version" in d


# --- TOML (Cargo, pyproject) -----------------------------------------------

def toml_sections(text, wanted):
    """Return (start, end) spans of the wanted [sections]."""
    spans, cur, start = [], None, 0
    for m in re.finditer(r"^\[([^\]]+)\]\s*$", text, re.M):
        if cur in wanted:
            spans.append((start, m.start()))
        cur, start = m[1].strip(), m.end()
    if cur in wanted:
        spans.append((start, len(text)))
    return spans


def toml_reader(label, sections):
    def read(path, text):
        rows = []
        for s, e in toml_sections(text, sections):
            body = text[s:e]
            m = re.search(r'^version\s*=\s*"([^"]+)"', body, re.M)
            if m:
                rows.append({"label": label, "version": m[1], "build": None})
            elif re.search(r'^dynamic\s*=.*"version"', body, re.M):
                rows.append({"label": f"{label} (dynamic: set by tag/plugin, not editable here)",
                             "version": None, "build": None})
        return rows
    return read


def toml_writer(sections):
    def write(text, version, build, platform):
        if not version:
            return text
        for s, e in reversed(toml_sections(text, sections)):
            text = text[:s] + sub_once(r'^(version\s*=\s*)"[^"]+"', rf'\g<1>"{version}"', text[s:e], re.M) + text[e:]
        return text
    return write


# --- .NET, plain VERSION file -----------------------------------------------

def read_dotnet(path, text):
    tag = lambda t: (re.search(rf"<{t}>([^<]+)</{t}>", text) or [None, None])[1]
    v = tag("ApplicationDisplayVersion") or tag("Version")
    b = tag("ApplicationVersion")
    return [{"label": "dotnet", "version": v, "build": b}] if (v or b) else []


def write_dotnet(text, version, build, platform):
    for t in ("ApplicationDisplayVersion", "Version"):
        if version:
            text = re.sub(rf"(<{t}>)[^<]+(</{t}>)", rf"\g<1>{version}\g<2>", text)
    if build is not None:
        text = re.sub(r"(<ApplicationVersion>)[^<]+(</ApplicationVersion>)", rf"\g<1>{build}\g<2>", text)
    return text


def read_file(path, text):
    v = text.strip()
    return [{"label": "VERSION file", "version": v, "build": None}] if re.fullmatch(r"\S+", v) else []


def write_file(text, version, build, platform):
    return f"{version}\n" if version else text


# kind, glob, reader, writer
SOURCES = [
    ("xcodegen", "project.yml", read_xcodegen, write_xcodegen),
    ("xcode", "project.pbxproj", read_xcode, write_xcode),
    ("gradle", "build.gradle*", read_gradle, write_gradle),
    ("flutter", "pubspec.yaml", read_flutter, write_flutter),
    ("expo", "app.json", read_expo, write_expo),
    ("npm", "package.json", json_version_reader("npm"), write_json_version),
    ("tauri", "tauri.conf.json", json_version_reader("tauri"), write_json_version),
    ("extension", "manifest.json", json_version_reader("extension", is_extension), write_json_version),
    ("cargo", "Cargo.toml", toml_reader("cargo", {"package", "workspace.package"}), toml_writer({"package", "workspace.package"})),
    ("python", "pyproject.toml", toml_reader("python", {"project", "tool.poetry"}), toml_writer({"project", "tool.poetry"})),
    ("dotnet", "*.csproj", read_dotnet, write_dotnet),
    ("file", "VERSION", read_file, write_file),
]


def scan(root):
    """Return [(kind, path, rows, writer)] for every versioned file."""
    found = []
    for kind, pattern, reader, writer in SOURCES:
        paths = [root / pattern] if kind == "file" else walk(root, pattern)
        for p in paths:
            if p.is_file():
                rows = reader(p, p.read_text(errors="ignore"))
                if rows:
                    found.append((kind, p, rows, writer))
    if any(k == "xcodegen" for k, *_ in found):  # the spec owns the numbers
        found = [f for f in found if f[0] != "xcode"]
    return found


def warnings(root):
    for p in walk(root, "Info.plist"):
        t = p.read_text(errors="ignore")
        for k in ("CFBundleShortVersionString", "CFBundleVersion"):
            m = re.search(rf"<key>{k}</key>\s*<string>([^<]+)</string>", t)
            if m and not m[1].startswith("$("):
                yield f"{p.relative_to(root)}: {k} is hardcoded ({m[1]}); build settings will not reach it"
    for p in walk(root, "eas.json"):
        if '"remote"' in p.read_text(errors="ignore"):
            yield f"{p.relative_to(root)}: appVersionSource is remote; EAS owns build numbers, don't edit them locally"
    for name in ("app.config.js", "app.config.ts"):
        for p in walk(root, name):
            yield f"{p.relative_to(root)}: dynamic Expo config; edit versions there by hand"


def show(root):
    found = scan(root)
    if not found:
        print("No version sources found. Versions may live only in git tags (Go modules, services).")
    for kind, p, rows, _ in found:
        print(f"## {p.relative_to(root)}  [{kind}]")
        for r in rows:
            print(f"  {r['label']:50} version={r['version']}  build={r['build']}")
    for w in warnings(root):
        print("WARN " + w)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["show", "bump-build", "set-version"])
    ap.add_argument("repo")
    ap.add_argument("version", nargs="?")
    ap.add_argument("--only", help="limit to one kind, e.g. gradle, npm, xcode")
    ap.add_argument("--platform", help="Apple SDK filter (ios, tvos, macos…); android = --only gradle")
    ap.add_argument("--path", help="only files whose relative path contains this")
    ap.add_argument("--to", type=int, help="bump-build: set this build number instead of +1")
    a = ap.parse_args()
    root = pathlib.Path(a.repo).resolve()

    if a.cmd == "show":
        return show(root)
    if a.cmd == "set-version" and not a.version:
        sys.exit("set-version needs a version, e.g. 1.0.1")
    if a.platform == "android":
        a.only, a.platform = "gradle", None

    found = [f for f in scan(root)
             if (not a.only or f[0] == a.only)
             and (not a.path or a.path in str(f[1].relative_to(root)))
             and (not a.platform or f[0] in APPLE)]
    if not found:
        sys.exit("no version file matched the filters")
    if a.cmd == "bump-build":
        found = [f for f in found if any(r["build"] for r in f[2])]
        if not found:
            sys.exit("no build number here: this project type is identified by its version alone")

    def nums(rows):
        return [int(n) for r in rows if r["build"] for n in re.findall(r"\d+", r["build"])]
    apple_next = max((n for k, _, rows, _ in found if k in APPLE for n in nums(rows)), default=0) + 1

    changed = False
    for kind, p, rows, writer in found:
        text = p.read_text()
        if a.cmd == "set-version":
            new, what = writer(text, a.version, None, a.platform), f"version -> {a.version}"
        else:
            build = a.to or (apple_next if kind in APPLE else max(nums(rows)) + 1)
            new, what = writer(text, None, build, a.platform), f"build -> {build}"
        if new != text:
            p.write_text(new)
            changed = True
            print(f"{p.relative_to(root)} [{kind}] {what}")
    if not changed:
        sys.exit("nothing changed (dynamic or already at that value); see `show`")


if __name__ == "__main__":
    main()
