# Telemetry detail redesign — design QA

Date: 2026-11-02. Initial scope: local preview development. Later, the owner authorized a private Spark package installation; see [live validation](docs/development/METRIC-DETAILS-LOCAL-VALIDATION.md). No GitHub push or public release.

## Source and comparison basis

- Source visual: `../verification/metric-details-20261102/reference-memory.png` (1619 × 971 PNG). This is the user's generated PC/mobile memory concept, used as information-layout inspiration, explicitly not a pixel-exact target.
- Existing product is the visual authority: dark square panels, thin borders, lime highlights, Chakra Petch / Rajdhani / SUIT and existing modal motion. No new logos, decorative illustrations or raster interface assets.
- Implementation: `http://127.0.0.1:8766/?lang=ko#overview`, loopback-only fixture preview outside the repository. Its banner and status labels identify example data. No fixture code is packaged.
- Final desktop evidence: `../verification/metric-details-20261102/final-desktop-memory.jpg`, `final-desktop-cpu.jpg`, `final-desktop-network.jpg` (each 1920 × 1080 pixels / CSS viewport, DPR approximately 1).
- Final mobile evidence: `../verification/metric-details-20261102/final-mobile-390-memory.jpg` (390 × 844 pixels / CSS viewport, DPR approximately 1); `final-mobile-320-diskio.jpg` and `mobile-320-memory-notes.jpg` (320 × 740).
- Earlier captures `desktop-*.jpg` use 1440 × 1050. Source and final desktop/mobile captures were viewed together in one comparison input. The source combines two artboard panels and has no CSS viewport or known device density; compare hierarchy and component treatment, not full-image pixel distances. Browser captures are 1:1 CSS pixels, not physical-device photographs.

## Findings and iteration history

1. **[P2, fixed] SVG intrinsic size exceeded its grid track.** An early desktop plot was 164px high but the SVG expanded to 184px, overlapping time labels. Constrain the plot area and position its SVG within that area. Reinspection confirmed equal plot/SVG height and separated labels; final evidence above shows clean axes.
2. **[P2, fixed] Existing generic modal definition-list CSS split the hardware rows.** Scope the new definition list as a block, with one label/value grid per row. Final desktop memory shows aligned installed/OS capacity rows; mobile notes and tables remain readable.
3. **[P2, fixed] A 190.0 MB/s reading clipped at 320px.** Use a 28px numeric size below 360px and compact decimal GB/s for headline rates above 1,000 MB/s. Rechecked 999.9 MB/s, 4.3 GB/s, 0.011 MB/s and 100% per-core readings: no clipped numeric cells or horizontal modal overflow.
4. **[P3, resolved] Duplicate header metadata and loose chart spacing.** Removed the redundant eyebrow, tightened stat/chart spacing and used a neutral available-memory bar. The result follows the existing product's density while retaining the concept's information order.

No remaining actionable P0/P1/P2 findings in the tested local states.

## Required visual surfaces

- **Typography:** existing self-hosted SUIT Korean, Chakra Petch English and Rajdhani numerals retained. Units remain visually secondary, values use tabular numerals, no number clipping in 320/390px stress cases. Main overview typography is unchanged.
- **Spacing/layout:** 4 summary columns on desktop and 2 on phones; fixed plot height; centered 980px desktop modal; sticky close row; one independently opened dialog per metric. Long content scrolls inside the dialog. The generated image's fully visible mobile artboard is intentionally adapted to a scrollable phone viewport, rather than shrinking all text to fit.
- **Colors/tokens:** existing CSS theme tokens; lime primary traces, purple secondary I/O, neutral available capacity, orange reserved storage and stale status. No gradients, glow or new rounded-card system.
- **Images/assets:** existing logo and SVG arrows unchanged. Charts use live vector geometry derived from API samples, not raster mockups or decorative approximations. No asset replacement was required.
- **Copy/content:** human labels and units replace raw JSON fields. Actual capacity governs memory/SSD axes. No invented whole-system power, per-process memory, CPU/SoC sensor identity, IOPS, latency or drive breakdown. Statistics distinguish missing values from zero and preserve collection gaps. Explicit Korean/English copy.

Focused inspection covered stat labels/numbers/units, y-axis and time labels, capacity legend, table rows, core tiles, close/range controls and the disclosure. Full modal and surrounding overview were also captured; no additional image-only crop was necessary at these 1:1 dimensions.

## Executed checks

- All eight dialogs open and close on desktop (1440px), 390px Korean and 320px English. Additional 1920 × 1080 desktop captures confirm centered layout. No horizontal modal overflow; four summary readings in each dialog.
- After the final narrow-width fix: 320px high-load CPU, 999.9 MB/s, 4.3 GB/s and small nonzero-rate cases pass numeric-fit checks. 390px summary retains two columns.
- 1m, 5m and 1h controls change the selected range; valid sample count reflects available history rather than claiming a complete hour.
- Expanded source notes, keyboard focus and scroll position survived multiple five-second updates (observed scroll position unchanged). Tab from the last disclosure returns to close; Escape closes and restores focus to the originating card.
- Disconnection fixture retains the last reading and marks updates stopped. Missing sensors show dashes/unknown, not zero or healthy. A zero-rate fixture retains real zero readings and a baseline trace.
- 64 GiB fixture shows 64.0 GiB installed / 60.8 GiB OS total and scales the chart to 60.8. A 12-logical-CPU fixture renders 12 tiles; no 128 GiB/20-core assumption.
- Reduced-motion browser emulation reported `prefers-reduced-motion: reduce` and zero active modal animations. Emulation was restored. Existing normal entry/exit timing remains 300/200ms.
- Browser console: no application errors in the final preview. Development inspection initially used a method unavailable in the tool's read-only DOM facade; the supported CDP inspection verified animation state instead.
- Intentionally blocking the new detail script showed a reload instruction instead of prototype fixture values. Removed the block, reloaded and verified normal GPU details. The resource failure in that test is intentional. Main overview mini-charts retain their own five-minute window independently of the dialog range.
- Node pure-data tests: 7/7 pass. All web JavaScript syntax checks and `git diff --check` pass.
- Linux backend regressions: 17/17 pass in an isolated temporary source directory on Spark; bash syntax checks pass. Existing dashboard/model services were not replaced or stopped. A read-only collector sample confirmed current field names, units and null memory-clock behavior.

## Residual limits

- iPhone Safari and Firefox were not run on physical devices in this change. Mobile checks use Chromium viewport emulation. No assertion of universal browser compatibility or measured inference overhead.
- At the initial preview review, Spark and GitHub were unchanged. Spark was subsequently updated under separate owner authorization to a private development package; the public release remains deferred. The live validation report records that later scope and evidence separately from the fixtures here.
- Backend collection remains the existing on-demand cache; no new polling or dependencies. No new cgroup memory benchmark was needed for the frontend-only patch, and none is claimed.

## Implementation checklist

- [x] Eight metric-specific dialogs and accurate units/capability states
- [x] Shared time controls, gap-aware charts and stable axes
- [x] Responsive summary grids, keyboard handling and preserved update state
- [x] Korean/English guides and source notes
- [x] Local visual/data/backend regression checks
- [ ] Physical Safari/Firefox validation before a public release
- [ ] Owner-requested release and deployment, deferred

Final result: **passed**

SSD follow-up: the owner subsequently removed the SSD history panel. The current SSD view is headline values, composition, mount point and collapsed accounting; the other seven charts remain. See the [private Spark follow-up record](docs/development/METRIC-DETAILS-LOCAL-VALIDATION.md#ssd-follow-up-022dev202611022) and fresh evidence under `../verification/ssd-detail-20261102/`. Earlier chart descriptions in this report describe the initial eight-chart version.

## Follow-up review — original chip retained

The owner cancelled the proposed GB10 artwork replacement. No generated chip asset was added to the application. The existing `deviceArt()` SVG is byte-for-byte identical to the function in HEAD; the dynamic hardware labels remain unchanged.

Reopened all eight detail dialogs at 1440 × 1000, 390 × 844 and 320 × 740. Desktop summaries retain four equal columns; both phone sizes retain two equal columns. The 24 measured states had no horizontal modal overflow or clipped headline values. Existing typography, colors, spacing and motion were retained; this review required no further application changes.

Fresh evidence is under `../verification/metric-review-gb10/` (the folder name predates the cancellation). `layout-checks.json` records the geometry checks. Visually reviewed `desktop-memory.jpg`, `desktop-temp.jpg`, `mobile-390-memory.jpg`, `mobile-390-diskio.jpg`, `mobile-390-power.jpg`, `mobile-320-diskio.jpg` and `mobile-320-temp.jpg`. These remain example-data captures from the loopback-only preview, not live Spark telemetry. The original artwork was also verified in `02-retained-chip-overview.jpg`.

Viewport overrides were reset. No GitHub upload, installed Spark change, model operation or new dependency was introduced. The physical Safari/Firefox validation limitation above still applies.
