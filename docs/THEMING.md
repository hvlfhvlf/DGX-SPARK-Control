# Theme contract

`web/theme.css` owns every interface color; `theme-init.js` applies validated browser preferences before paint. The default is black/lime. `preferences.js` persists mode and accent without rerendering forms or resetting telemetry.

- Use `--bg`, `--surface`, `--raised`, `--line`, `--text`, `--muted` for surfaces and typography.
- Use `--accent` for text, focus rings and primary chart lines; `--accent-fill` with `--on-accent` for filled controls. These differ in white mode.
- Use `--chart-secondary` for the second data series. Its hue remains distinct for each preset.
- Use `--warning`, `--warning-soft`, `--danger`, `--danger-fill`, `--danger-soft`, `--on-danger` for semantic status. Do not recolor errors as an accent.
- SVG icons use `currentColor`; decorative chip artwork uses `--art-*`. Keep its geometry unchanged.
- Hover foregrounds and surfaces use paired `--hover-*` variables.
- Add future colors to the palette, never inline hex/rgb in components. The theme regression test rejects component color literals.
- Verify all six mode/preset combinations, normal/selected/hover/disabled/error/modal states, KO/EN, and 320/390 px phone widths. Do not shrink telemetry below two columns.
- Run `node --test tests/theme.test.cjs` and the existing JavaScript suite. Contrast tests cover core palette pairs; they are not a substitute for rendered accessibility checks.
- No dependency, background worker, telemetry request or external font is added by theming.
