# AWS Periodic Table — Design Spec

**Date:** 2026-06-26  
**Author:** Lars Marin  
**Status:** Approved

---

## Context

Public tool at tecracer.com. Lambda runs monthly, fetches AWS service data from three sources (web scraping, Directory API, ESC filter), renders Mustache templates into self-contained HTML, uploads to S3 + CloudFront. ~300 AWS services displayed in a 19-column periodic table grid with tabs for Global (Scraping), Global (Directory), and European Sovereign Cloud.

**Audience:** Public — AWS practitioners, customers, anyone referencing AWS services.

---

## Goals

1. Fix data quality issues (silent failures, stale data, broken matching)
2. Make the UI usable on mobile and tablet devices
3. Add PWA support (installable without App Store)
4. Ship desktop native builds (Windows, macOS, Linux) via Tauri
5. Ship store apps (iOS App Store, Google Play) via Capacitor

Phases are independent and deliver value incrementally. Each can be shipped separately.

---

## Phase 1a — Data Quality Fixes

### Problem 1: ESC Matching Failures

`get_data_from_esc()` tries 4 name variants for matching but 3 services in `esc_services.json` lack prefix (`EC2 Image Builder`, `Elastic Load Balancing`, `Service Quotas`). The `full_name` field (e.g. `"AWS EC2 Image Builder"`) does not match `"EC2 Image Builder"`.

**Fix:** Normalize both sides before comparison — strip `AWS ` / `Amazon ` prefix from both the service name and each ESC list entry before matching.

### Problem 2: Directory API Silent Truncation

`PERIODIC_PRODUCTS_SIZE` defaults to 300. If AWS returns exactly 300 items, services beyond that are silently dropped.

**Fix:** After fetch, if `len(items) == requested_size`, log a warning. Add pagination support using the API's `from` parameter, fetching in pages of 100 until no more items are returned.

### Problem 3: `reserved_symbols` Stale

~35 manually maintained entries. New services get auto-generated symbols that may be unintuitive or collide.

**Fix:** Add `debug/audit_symbols.py` — runs the symbol generator over all live services and prints: collisions, services using fallback sequence, entries in `reserved_symbols` that no longer match any live service.

### Problem 4: Scraping Silent Failure

`get_data_from_scrape()` parses `globalNav` JSON from `aws.amazon.com/products/`. If AWS changes page structure, returns empty or partial data with no alert.

**Fix:** After scraping, if `total_services < 100`, raise an exception (Lambda will log and alarm via CloudWatch). Add this guard in `lambda_handler.py`.

### Problem 5: Stale ESC Fallback JSON

`esc_services.json` has no timestamp. If dynamic fetch from `docs.aws.eu` fails, the fallback may be months old.

**Fix:** Add `"updated": "2026-06-26"` field to `esc_services.json`. Lambda reads this field after falling back and logs a warning if age > 30 days.

### Problem 6: `preferred_names` Too Small

Only 2 entries. Many services trigger `ReallySmallName` (>20 chars) and are hard to read in 4vw cells.

**Fix:** Add `debug/audit_long_names.py` — lists all services where `len(clean_name) > 20`, sorted by length. Review output manually and extend `preferred_names` with sensible abbreviations.

---

## Phase 1b — Responsive Design

### Strategy: Horizontal Scroll (not reflow)

A 19-column periodic table cannot reflow to mobile widths — the grid structure is the product. On narrow screens, the grid scrolls horizontally with a sensible minimum cell size.

### CSS Changes (`base_template.mustache`)

**Desktop (≥1024px):** No change — all existing `vw` units preserved.

**Tablet (768px–1023px):**
```css
@media (max-width: 1023px) {
  .Wrapper { width: 98%; overflow-x: auto; }
  .Grid {
    grid-template-columns: repeat(19, 44px);
    grid-template-rows: repeat({{grid_rows}}, 44px);
    grid-column-gap: 4px;
    grid-row-gap: 4px;
  }
  .Service { width: 44px; height: 44px; border-radius: 4px; }
  .Symbol { font-size: 22px; }
  .Name { font-size: 9px; }
  .SmallName { font-size: 7px; }
  .ReallySmallName { font-size: 6px; }
  .Prefix { font-size: 6px; }
}
```

**Mobile (<768px):**
```css
@media (max-width: 767px) {
  .Wrapper { width: 100%; padding: 0 8px; overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .Grid {
    grid-template-columns: repeat(19, 36px);
    grid-template-rows: repeat({{grid_rows}}, 36px);
    grid-column-gap: 3px;
    grid-row-gap: 3px;
  }
  .Service { width: 36px; height: 36px; border-radius: 3px; touch-action: manipulation; }
  .Symbol { font-size: 18px; }
  .Name { font-size: 7px; }
  .SmallName { font-size: 6px; }
  .ReallySmallName { font-size: 5px; }
  .Prefix { font-size: 5px; }
  .Header { flex-direction: column; align-items: center; font-size: clamp(14px, 4vw, 24px); }
  .tabs { flex-wrap: wrap; gap: 8px; justify-content: center; }
  .tab { font-size: 13px; padding: 8px 14px; }
}
```

**Typography:** Header `font-size` from `1.75vw` to `clamp(14px, 1.75vw, 28px)` — prevents text becoming invisible on small screens.

### Template Cleanup

`template.mustache` is a legacy file no longer used by `lambda_handler.py`. Delete it. All work targets `base_template.mustache` only.

---

## Phase 2 — PWA

### Deliverables

**`manifest.json`** (generated by Lambda, uploaded to S3):
```json
{
  "name": "Periodic Table of Amazon Web Services",
  "short_name": "AWS Table",
  "description": "All AWS services in one periodic table",
  "start_url": "/index.html",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#f86b00",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

**`sw.js`** (Service Worker, uploaded to S3):
- Caches all 4 HTML files + manifest on first visit
- Serves from cache when offline
- Cache key includes a version string (`CACHE_VERSION`) set to the Lambda execution date (ISO format, e.g. `2026-06-26`) — written into `sw.js` by Lambda at generation time, forcing cache refresh on each monthly run

**Icons:** `icon-192.png` and `icon-512.png` resized from existing `favicon.png` using Pillow. Resize is a one-time local step in `create_base64_images.py` (Pillow added to `requirements.txt` for local dev only — not needed in Lambda). Output committed to `periodic/img/`, uploaded to S3 root by Lambda alongside HTML files.

**Template additions (`base_template.mustache`):**
```html
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#f86b00">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="AWS Table">
<link rel="apple-touch-icon" href="/icon-192.png">
<script>
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js');
  }
</script>
```

### IAM Policy Update

`infrastructure/template.yaml` S3 PutObject policy must include:
- `${Bucket}/manifest.json`
- `${Bucket}/sw.js`
- `${Bucket}/icon-192.png`
- `${Bucket}/icon-512.png`

---

## Phase 3 — Desktop Native (Tauri)

### Architecture

Tauri wraps the live URL in a native window — no second frontend codebase.

```
aws-periodic-desktop/
├── src-tauri/
│   ├── tauri.conf.json
│   ├── Cargo.toml
│   └── src/main.rs
```

`tauri.conf.json` sets `"url": "https://your-domain.com"` (Modus A — URL-based, always current, requires internet). Offline bundle (Modus B) deferred until explicitly required.

**Window config:** 1400×900 default, resizable, min 800×600.

### Build & Distribution

New GitHub Actions workflow `.github/workflows/desktop-release.yml`:

| Runner | Output |
|--------|--------|
| `ubuntu-latest` | `.AppImage`, `.deb` |
| `windows-latest` | `.exe` (NSIS installer) |
| `macos-latest` | `.dmg` (Universal Binary) |

Triggered on git tag `desktop-v*`. Artifacts published to GitHub Releases.

**macOS Notarization:** Optional. Without it, Gatekeeper shows a warning on first launch. Users can bypass with right-click → Open. Add notarization when Apple Developer account is available.

**Windows Code Signing:** Optional. SmartScreen warning on first install without signing certificate.

---

## Phase 4 — Store App (Capacitor)

### Architecture

Capacitor wraps the same HTML in native iOS/Android WebViews. The app loads the live URL (no bundled HTML — avoids App Store re-review on content updates).

```
aws-periodic-mobile/
├── capacitor.config.json   ← points to live URL
├── ios/                    ← generated Xcode project
└── android/                ← generated Android Studio project
```

### Requirements

| | iOS | Android |
|---|---|---|
| Account | Apple Developer ($99/yr) | Google Play ($25 one-time) |
| Toolchain | Xcode on macOS | Android Studio |
| Signing | Certificates + Provisioning Profiles | Keystore |
| Review | 1–3 days | Hours–1 day |

### Build Pipeline

Manual trigger via GitHub Actions:
- iOS: `macos-latest` runner, Xcode build, signed `.ipa`, uploaded to App Store Connect via `altool`
- Android: `ubuntu-latest`, Gradle build, signed `.aab`, uploaded to Google Play via `fastlane`

Signing secrets stored in GitHub Actions secrets.

### Decision Criteria

Store apps are justified when:
- App Store discoverability is a business requirement
- Push notifications are planned
- Customers explicitly request a store-installable app

Otherwise, PWA + "Add to Home Screen" achieves equivalent UX with zero store overhead.

---

## Out of Scope

- Backend API separation (Lambda continues to generate HTML directly)
- React Native / Flutter rewrite
- Real-time AWS service updates (monthly Lambda cadence is sufficient)
- Multi-language support

---

## Phased Delivery Order

| Phase | Scope | Effort | Value |
|-------|-------|--------|-------|
| 1a | Data quality fixes | S | High — correctness |
| 1b | Responsive CSS + template cleanup | M | High — mobile usability |
| 2 | PWA | S | High — installable everywhere |
| 3 | Tauri desktop | M | Medium — desktop native |
| 4 | Capacitor store | L | Low–Medium — only if store presence needed |
