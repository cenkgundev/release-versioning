# Channel rules

What each store, registry and format accepts. Read the sections for the channels the project ships to.

- [Apple App Store, TestFlight, Mac App Store](#apple)
- [Google Play](#google-play)
- [Other mobile stores](#other-mobile-stores)
- [Cross-platform mobile frameworks](#cross-platform-mobile)
- [Desktop, direct download](#desktop-direct-download)
- [Microsoft Store, MSIX, Windows installers](#windows)
- [Package registries](#package-registries)
- [Web apps and services](#web-apps-and-services)
- [Browser extensions](#browser-extensions)
- [Games](#games)

## Apple

- `CFBundleShortVersionString` (`MARKETING_VERSION`): up to three non-negative integers, `1.3.1`. No letters or pre-release suffixes.
- `CFBundleVersion` (`CURRENT_PROJECT_VERSION`): up to three integers; a single integer is simplest. Must be unique and increasing within a version; using one counter across all versions avoids collisions.
- Once a version is approved/released, that train is closed. Further uploads need a higher version.
- While a version is in review or rejected, upload another build of the same version.
- iOS, tvOS, visionOS and macOS on one app record have separate version trains.
- App extensions (widgets, intents, top shelf, watch apps) must match the host app's version and build, or upload validation fails.
- Info.plist must reference `$(MARKETING_VERSION)` / `$(CURRENT_PROJECT_VERSION)`. A hardcoded value silently wins over build settings.

## Google Play

- `versionCode`: integer, strictly greater than every code ever uploaded for the package, across all tracks. Max 2100000000.
- `versionName`: free-form display string; use `MAJOR.MINOR.PATCH`.
- A rejected or halted release still consumed its versionCode; the next upload needs a higher one.
- Several APKs/bundles for one release (Wear OS, TV, ABI splits) need distinct versionCodes. A common scheme is a per-variant offset, e.g. `versionCode = base * 10 + variant`.

## Other mobile stores

Huawei AppGallery, Samsung Galaxy Store and Amazon Appstore use the Android `versionCode` / `versionName` rules. A higher versionCode on one store doesn't block another, but keeping one counter avoids confusion.

## Cross-platform mobile

- **Flutter**: `pubspec.yaml` `version: 1.3.1+167` → version `1.3.1`, build `167` for both iOS and Android. `--build-name` / `--build-number` flags override it at build time.
- **React Native (bare)**: native files are the truth (`ios/*.xcodeproj` or XcodeGen, `android/app/build.gradle`). `package.json` version is unused by the stores; keep it in sync only if the project already does.
- **Expo**: `app.json` `expo.version`, `expo.ios.buildNumber` (string), `expo.android.versionCode` (int). If `eas.json` has `"appVersionSource": "remote"` or `autoIncrement`, EAS owns build numbers; don't edit them locally.
- **.NET MAUI**: `ApplicationDisplayVersion` (version) and `ApplicationVersion` (integer build) in the `.csproj`.
- **Kotlin Multiplatform / Compose Multiplatform**: each platform's native file (Xcode, Gradle); desktop uses `packageVersion` in `compose.desktop` (MAJOR > 0 required for macOS packaging).

## Desktop, direct download

- The auto-updater compares versions, usually as SemVer (Electron `electron-updater`, Tauri updater, Sparkle). Never ship a lower or equal version to the same channel.
- Pre-releases (`1.4.0-beta.2`) are fine if the updater has a beta channel. Sparkle compares `CFBundleVersion`, so the build number must increase too.
- macOS bundles still carry `CFBundleShortVersionString` + `CFBundleVersion`. Notarization doesn't care about the numbers, but Sparkle and the Finder do.
- Electron: `package.json` `version`; electron-builder takes `buildVersion` for the macOS build number and Windows file version.
- Tauri: `tauri.conf.json` `version` (or taken from `Cargo.toml` when omitted).

## Windows

- MSIX / Microsoft Store: four parts `MAJOR.MINOR.BUILD.REVISION`, each 0–65535. For Store submissions the last part must be `0`. Map `1.3.1` + build 167 to `1.3.167.0` or `1.3.1.0`; pick one convention per app and record it in VERSIONING.md.
- Win32 file/product version (VERSIONINFO, MSI `ProductVersion`): MSI compares only the first three parts for upgrades, so the third part must change between releases.

## Package registries

All of these are immutable: a published version can be yanked or deprecated, never replaced. A fix is always a new version.

- **npm**: strict SemVer. Pre-releases `1.0.0-beta.1`, published with `--tag beta` so `latest` doesn't move. `npm version <patch|minor|major>` bumps, commits and tags in one step; use it if the project already does. In `0.y.z`, `^0.3.0` allows only `0.3.x`, so a MINOR in 0.x is breaking for users.
- **PyPI**: PEP 440, not SemVer syntax. Pre-releases `1.0.0a1`, `1.0.0b1`, `1.0.0rc1`; post-releases `1.0.0.post1`; dev `1.0.0.dev3`. `setuptools_scm` / `hatch-vcs` derive the version from git tags: then the tag is the version.
- **crates.io**: SemVer. Cargo treats `0.y` minor bumps as breaking (`^0.3` = `>=0.3.0, <0.4.0`). Workspaces may share `[workspace.package] version`.
- **Maven Central**: release versions immutable; `-SNAPSHOT` only for snapshot repos. Gradle `version = "1.3.1"` or `gradle.properties` `VERSION_NAME`.
- **NuGet**: SemVer 2.0; `<Version>` or `<PackageVersion>` in the `.csproj`.
- **Go modules**: no file; the git tag `vX.Y.Z` is the version. From v2 on, the module path must end in `/v2` and imports change. A MAJOR bump is a code change, not just a tag.
- **CocoaPods / Swift Package Manager**: SPM resolves git tags as versions (`1.2.3` and `v1.2.3` both work; follow the repo's existing tags); the podspec `s.version` must match the tag.
- **Homebrew, apt, other distro packages**: track the upstream version; packaging-only changes use the packager's revision field.

## Web apps and services

- Users never see a store version, so continuous deploys don't need version bumps. Identify deploys by commit SHA or deploy ID.
- Tag a version when there is a release people refer to: a launch, a changelog entry, a client that must know what it talks to, an on-prem/self-hosted distribution.
- Container images: tag with the version (`1.3.1`, `1.3`, `1`) and the SHA. Avoid moving `latest` in production.
- Public HTTP APIs: the contract version (`/v1`, `/v2`, header) changes only on breaking changes and is separate from the release version.
- Web clients that must refresh (PWA, SPA cache busting) can surface `version+sha` in an about screen or `/version` endpoint.

## Browser extensions

- Chrome Web Store / Edge: `manifest.json` `version` is one to four dot-separated integers, each 0–65535, no letters. Each upload must be higher. `version_name` is an optional display string (`1.3.1 beta`).
- Firefox (AMO): same format recommended; must increase per listed upload.
- Safari web extensions ship inside an Apple app; Apple rules apply.

## Games

- **Steam**: no enforced version format; each upload gets a BuildID automatically. Show your own version in-game and in patch notes. Beta branches carry the next version with a pre-release label.
- **Console platforms** have their own submission versioning (patch numbers, title updates) defined in their SDK docs; follow those and map them to the public version in VERSIONING.md.
- Engine settings: Unity `PlayerSettings.bundleVersion` + Android `bundleVersionCode` / iOS `buildNumber`; Unreal `ProjectVersion` in `DefaultGame.ini`; Godot `application/config/version` plus export-preset version codes. Edit these in the engine or by hand; the helper doesn't read them.
