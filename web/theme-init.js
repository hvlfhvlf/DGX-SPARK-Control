/* Runs before paint; no network, timers or system preferences. */
'use strict';
(() => {
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem('spark.preferences.v1') || '{}') || {}; } catch (_) {}
  document.documentElement.dataset.theme = saved.theme === 'white' ? 'white' : 'black';
  document.documentElement.dataset.accent = ['lime','lavender','ice'].includes(saved.accent) ? saved.accent : 'lime';
})();
