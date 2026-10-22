---
name: app-versioning
description: Decide and apply version numbers (1.0.0, 1.0.1, 1.1.0…) and build numbers for iOS, iPadOS, tvOS, macOS and Android apps. Use whenever a TestFlight / Play internal upload, App Store or Play submission, hotfix, rejection resubmit, or release is being prepared, whenever MARKETING_VERSION, CURRENT_PROJECT_VERSION, CFBundleShortVersionString, CFBundleVersion, versionName or versionCode would change, and whenever the user asks which version to use, to bump the version or build number, "1.0.1 or 1.1.0?" (in any language), or about git tags / changelog for an app release. Also use before archiving or uploading any build, even if versioning isn't mentioned, so numbers are never bumped ad hoc.
---

# App versioning

Two numbers, two jobs:

- **Version** (`MARKETING_VERSION` / `versionName`), `MAJOR.MINOR.PATCH`: what users see in the store. Only moves when a build is headed to the public store, and only with the user's approval.
- **Build** (`CURRENT_PROJECT_VERSION` / `versionCode`): a single integer counter per app that only goes up and is never reset. Every upload (TestFlight, Play internal, store) gets a new one. Bump it freely.

Why: frequent pre-release uploads tend to inflate the version (an app that never shipped ends up at 1.9.0). Stores only need a fresh build number for each upload; the version is a promise to users and belongs to the user to decide.

## 1. Find the current state

Run the helper bundled with this skill (`<skill-dir>` is the folder holding this SKILL.md; needs only Python 3). It reads XcodeGen `project.yml`, `.pbxproj` and Gradle files:

```bash
python3 <skill-dir>/scripts/appver.py show <repo>
```

Then establish the **store state** for each platform, because the rules depend on it:

| State | How to tell |
|---|---|
| Unreleased | no version has ever been approved/live in that store |
| In review / waiting | a version is submitted but not live |
| Live | a version is Ready for Sale / in production |

Sources, in order: the repo's `VERSIONING.md`; App Store Connect / Play Console (CLI or API if available); project notes; otherwise ask the user in one line. Also note the **last uploaded build number** — the store may already have a higher build than the project file (archives built with overrides). The next build must exceed every build ever uploaded for that app.

## 2. Decide

**Unreleased app**
- Version stays `1.0.0` until the first public release. Every TestFlight/internal upload: bump build only.
- If the project currently says something else (0.1.0, 1.8.0…), don't change it silently; propose resetting to `1.0.0` before the first store submission, since the first store version can be anything.

**Version in review / waiting for review**
- Rejected, or a fix needed before it goes live: same version, new build. Apple and Google accept a new build for a version that isn't live yet.
- New work that continues meanwhile targets the next version, but don't set it until that work is actually headed to the store.

**Live app — next release**
Look at what changed since the live version's tag (`git log v<live>..HEAD`, CHANGELOG `Unreleased`), then propose:

| Bump | When | Example |
|---|---|---|
| PATCH 1.2.0 → 1.2.1 | bug fixes, crash fixes, copy/translation fixes, small polish, performance; no new user-facing capability | login fix |
| MINOR 1.2.1 → 1.3.0 | new feature, screen, setting, platform capability (widget, CarPlay, iPad layout), new paid tier, noticeable UX change | favorites + search |
| MAJOR 1.x → 2.0.0 | redesign, rebuilt app, business-model change (paid → subscription), dropping a big OS/device range, data/account migration users will notice | full redesign |

Mixed release: take the highest applicable bump. When unsure between PATCH and MINOR, ask yourself whether release notes would mention something *new* — if yes, MINOR.

PATCH resets nothing; MINOR resets PATCH to 0; MAJOR resets MINOR and PATCH to 0. Always three parts (`1.3.0`, not `1.3`). An app currently on a two-part version (`1.0`) moves to three parts at its next version change.

**Multiple platforms of one app**
- Same codebase and same features (iOS + iPadOS, universal): one version.
- iOS and Android with feature parity: keep versions aligned when convenient; versions may diverge if one platform ships a fix alone (iOS 1.2.1, Android 1.2.0 is fine).
- Separate store trains (tvOS vs iOS on one bundle id, desktop vs mobile) keep separate version lines. Build counter stays shared per app record.
- App extensions (widgets, top-shelf, watch) always carry the same version and build as their host app; the helper moves them together.

## 3. Propose and get approval

Version changes need explicit approval. Present one short block, in the user's language:

```
MyApp iOS: 1.3.0 live → proposed 1.3.1 (PATCH: fixes only — playback crash, translation typos)
Build: 166 → 167
OK?
```

Build-only bumps for test uploads need no approval; mention them in one line ("build 167, version stays 1.0.0").

## 4. Apply

```bash
python3 <skill-dir>/scripts/appver.py bump-build <repo> [--platform ios|tvos|macos|android] [--to N]
python3 <skill-dir>/scripts/appver.py set-version <repo> 1.3.1 [--platform ...]
```

- Use `--to N` when the store already has a build ≥ the project's number.
- XcodeGen projects: the helper edits `project.yml`; run `xcodegen generate` afterwards.
- If `show` warns about a hardcoded `CFBundleVersion`/`CFBundleShortVersionString` in an Info.plist, point it at `$(CURRENT_PROJECT_VERSION)` / `$(MARKETING_VERSION)` so the build settings reach the binary.
- Re-run `show` to confirm, then commit the bump on its own: `chore(release): 1.3.1 (167)` or `chore: build 167`.

## 5. Record

Keep three things in the repo; create them on first use from `references/templates.md`.

- **`VERSIONING.md`** — one table per platform: live version, version in review, last uploaded build, plus a short history log. Update it on every upload and every store state change. This is what step 1 reads next time, so the state never has to be guessed.
- **`CHANGELOG.md`** — Keep-a-Changelog style. Collect changes under `## [Unreleased]`; on a store submission rename that heading to `## [1.3.1] - YYYY-MM-DD`. Short, user-facing lines. The store's "What's New" text can be drawn from here.
- **Git tag** — on each **store submission** (not on TestFlight-only uploads), an annotated tag on the submitted commit: `git tag -a v1.3.1+167 -m "iOS 1.3.1 (167) submitted"`. Platform-specific lines get a prefix: `ios/v1.3.1+167`, `tvos/v1.0.1+161`, `android/v1.3.1+42`. If the submission is rejected and a new build goes in, add a new tag for the new build; keep the old one. Push tags only when the user pushes.

## Quick reference

| Situation | Version | Build |
|---|---|---|
| New TestFlight build, app never released | stays 1.0.0 | +1 |
| First store submission | 1.0.0 (confirm) | +1, tag |
| Rejected, resubmitting | same | +1, new tag |
| Fix for a live version | PATCH (propose) | +1 |
| New feature for a live app | MINOR (propose) | +1 |
| TestFlight of an upcoming release of a live app | the proposed next version, once approved | +1 |
