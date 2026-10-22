#!/usr/bin/env python3
"""Read and change app version numbers in Xcode and Gradle projects.

  appver.py show <repo>
  appver.py bump-build <repo> [--platform ios|tvos|macos|watchos|android] [--to N]
  appver.py set-version <repo> X.Y.Z [--platform ...]

Xcode: edits MARKETING_VERSION / CURRENT_PROJECT_VERSION in every
XCBuildConfiguration that ships (has a bundle id, not a test target) and
matches --platform. Extensions on the same platform move together with
their app, which App Store validation requires.
XcodeGen: when project.yml sets the versions, it is the source of truth;
it is edited instead of the pbxproj, then run `xcodegen generate`.
Gradle: edits versionCode / versionName in app-level build.gradle(.kts).
"""
import re, sys, pathlib, argparse

# .claude: agent worktrees; dist: exported archives
SKIP_DIRS = {"build", "DerivedData", "Pods", ".git", "node_modules", ".build", ".claude", "dist"}
SDK_TO_PLATFORM = {"iphoneos": "ios", "appletvos": "tvos", "macosx": "macos", "watchos": "watchos", "xros": "visionos"}


def walk(root, pattern):
    for p in root.rglob(pattern):
        if not SKIP_DIRS.intersection(p.parts) and not any(x.endswith(".xcarchive") for x in p.parts):
            yield p


def xcode_blocks(text):
    """Yield (start, end, settings) for each XCBuildConfiguration buildSettings block."""
    for m in re.finditer(r"isa = XCBuildConfiguration;\s*buildSettings = \{(.*?)\n\t\t\t\};", text, re.S):
        body = m.group(1)
        get = lambda k: (re.search(rf"\b{k} = \"?([^\";]+)\"?;", body) or [None, None])[1]
        bundle = get("PRODUCT_BUNDLE_IDENTIFIER")
        if not bundle or re.search(r"tests?$", bundle, re.I):
            continue
        sdk = get("SDKROOT") or ""
        platform = SDK_TO_PLATFORM.get(sdk, sdk or "?")
        yield m.start(1), m.end(1), {
            "bundle": bundle, "platform": platform,
            "version": get("MARKETING_VERSION"), "build": get("CURRENT_PROJECT_VERSION"),
        }


def gradle_files(root):
    for p in list(walk(root, "build.gradle.kts")) + list(walk(root, "build.gradle")):
        if re.search(r"versionCode", p.read_text()):
            yield p


def xcodegen_specs(root):
    for y in walk(root, "project.yml"):
        if re.search(r"^\s*(MARKETING_VERSION|CURRENT_PROJECT_VERSION):", y.read_text(), re.M):
            yield y


def show(root):
    for y in xcodegen_specs(root):
        t = y.read_text()
        for k in ("MARKETING_VERSION", "CURRENT_PROJECT_VERSION"):
            vals = sorted(set(re.findall(rf"^\s*{k}:\s*\"?([^\"\n]+)\"?", t, re.M)))
            print(f"## {y.relative_to(root)} (XcodeGen, source of truth)  {k}={', '.join(vals)}")
    for pbx in walk(root, "project.pbxproj"):
        print(f"## {pbx.relative_to(root)}")
        seen = {}
        for _, _, s in xcode_blocks(pbx.read_text()):
            key = (s["platform"], s["bundle"], s["version"], s["build"])
            seen[key] = seen.get(key, 0) + 1
        for (plat, bundle, ver, build), n in sorted(seen.items()):
            print(f"  {plat:8} {bundle:45} version={ver}  build={build}  ({n} configs)")
    for g in gradle_files(root):
        t = g.read_text()
        code = re.search(r"versionCode\s*=?\s*(\d+)", t)
        name = re.search(r"versionName\s*=?\s*\"([^\"]+)\"", t)
        print(f"## {g.relative_to(root)}\n  android  versionName={name and name[1]}  versionCode={code and code[1]}")
    for plist in walk(root, "Info.plist"):
        t = plist.read_text(errors="ignore")
        for k in ("CFBundleShortVersionString", "CFBundleVersion"):
            m = re.search(rf"<key>{k}</key>\s*<string>([^<]+)</string>", t)
            if m and not m[1].startswith("$("):
                print(f"WARN {plist.relative_to(root)}: {k} is hardcoded ({m[1]}); build settings will not reach it")


def edit_xcode(root, platform, key, value_fn):
    changed = []
    for pbx in walk(root, "project.pbxproj"):
        text = pbx.read_text()
        out, last = [], 0
        for start, end, s in xcode_blocks(text):
            if platform and s["platform"] != platform:
                continue
            body = text[start:end]
            new = re.sub(rf"(\b{key} = )\"?[^\";]+\"?;", lambda m: f"{m[1]}{value_fn(s)};", body)
            if new != body:
                changed.append(f"{pbx.relative_to(root)} {s['platform']} {s['bundle']}")
            out += [text[last:start], new]
            last = end
        out.append(text[last:])
        pbx.write_text("".join(out))
    return changed


def max_build(root, platform):
    builds = []
    for pbx in walk(root, "project.pbxproj"):
        for _, _, s in xcode_blocks(pbx.read_text()):
            if s["build"] and s["build"].isdigit():  # one counter across platforms
                builds.append(int(s["build"]))
    return max(builds) if builds else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["show", "bump-build", "set-version"])
    ap.add_argument("repo")
    ap.add_argument("version", nargs="?")
    ap.add_argument("--platform")
    ap.add_argument("--to", type=int, help="bump-build: set this build number instead of max+1")
    a = ap.parse_args()
    root = pathlib.Path(a.repo).resolve()

    if a.cmd == "show":
        return show(root)

    apple = a.platform != "android"
    android = a.platform in (None, "android")
    if a.cmd == "set-version" and not re.fullmatch(r"\d+\.\d+\.\d+", a.version or ""):
        sys.exit("version must be MAJOR.MINOR.PATCH, e.g. 1.0.1")

    specs = list(xcodegen_specs(root)) if apple else []
    if specs:
        key = "CURRENT_PROJECT_VERSION" if a.cmd == "bump-build" else "MARKETING_VERSION"
        for y in specs:
            t = y.read_text()
            if a.cmd == "bump-build":
                nxt = a.to or max(int(v) for v in re.findall(rf"^\s*{key}:\s*\"?(\d+)", t, re.M)) + 1
            else:
                nxt = a.version
            y.write_text(re.sub(rf"^(\s*{key}:\s*)\"?[^\"\n]+\"?", lambda m: f'{m[1]}"{nxt}"', t, flags=re.M))
            print(f"{y.relative_to(root)}: {key} -> {nxt}  (run `xcodegen generate`)")
        apple = False
    if apple:
        plat = a.platform
        if a.cmd == "bump-build":
            nxt = a.to or max_build(root, plat) + 1
            changed = edit_xcode(root, plat, "CURRENT_PROJECT_VERSION", lambda s: nxt)
            print(f"build -> {nxt}")
        else:
            changed = edit_xcode(root, plat, "MARKETING_VERSION", lambda s: a.version)
            print(f"version -> {a.version}")
        for c in sorted(set(changed)):
            print("  " + c)
    if android:
        for g in gradle_files(root):
            t = g.read_text()
            if a.cmd == "bump-build":
                t = re.sub(r"(versionCode\s*=?\s*)(\d+)", lambda m: f"{m[1]}{a.to or int(m[2]) + 1}", t)
            else:
                t = re.sub(r"(versionName\s*=?\s*)\"[^\"]+\"", lambda m: f'{m[1]}"{a.version}"', t)
            g.write_text(t)
            print(f"  {g.relative_to(root)} updated")


if __name__ == "__main__":
    main()
