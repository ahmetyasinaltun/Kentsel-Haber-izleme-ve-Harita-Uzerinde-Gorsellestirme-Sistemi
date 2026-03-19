// Filtre mantığı
/**
 * filters.js — Filtre paneli mantığı
 * UI kontrollerini yönetir; değişiklik olduğunda onFilterChange(filters) callback'ini çağırır.
 */

import { fetchFilterOptions } from "./api.js";

// Dışarıdan set edilebilen callback
let _onFilterChange = () => {};

// Mevcut filtre durumu
let _state = {
  news_type: "",
  district: "",
  date_from: "",
  date_to: "",
};

// ─── İlklendirme ─────────────────────────────────────────────────────────────
export async function initFilters(onFilterChange) {
  _onFilterChange = onFilterChange;

  // Tarih varsayılanları: son 3 gün
  const today = new Date();
  const threeDaysAgo = new Date(today);
  threeDaysAgo.setDate(today.getDate() - 3);

  const dateFromEl = document.getElementById("filter-date-from");
  const dateToEl   = document.getElementById("filter-date-to");

  if (dateFromEl) dateFromEl.value = _formatDate(threeDaysAgo);
  if (dateToEl)   dateToEl.value   = _formatDate(today);

  _state.date_from = dateFromEl?.value || "";
  _state.date_to   = dateToEl?.value   || "";

  // Seçenekleri sunucudan yükle
  try {
    const opts = await fetchFilterOptions();
    _populateSelect("filter-news-type", opts.news_types || [], "Tüm Türler");
    _populateSelect("filter-district",  opts.districts  || [], "Tüm İlçeler");
  } catch (e) {
    console.warn("Filtre seçenekleri yüklenemedi:", e.message);
    // Yedek: sabit kategoriler
    _populateSelect("filter-news-type", [
      "Trafik Kazası", "Yangın", "Elektrik Kesintisi", "Hırsızlık", "Kültürel Etkinlik"
    ], "Tüm Türler");
  }

  _bindEvents();
}

// ─── Event bağlama ────────────────────────────────────────────────────────────
function _bindEvents() {
  const ids = ["filter-news-type", "filter-district", "filter-date-from", "filter-date-to"];

  ids.forEach((id) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener("change", () => {
      _state.news_type  = document.getElementById("filter-news-type")?.value  || "";
      _state.district   = document.getElementById("filter-district")?.value   || "";
      _state.date_from  = document.getElementById("filter-date-from")?.value  || "";
      _state.date_to    = document.getElementById("filter-date-to")?.value    || "";
      _onFilterChange({ ..._state });
    });
  });

  // Filtreyi sıfırla butonu
  const resetBtn = document.getElementById("btn-reset-filters");
  if (resetBtn) {
    resetBtn.addEventListener("click", resetFilters);
  }
}

// ─── Dışa açık: filtreleri sıfırla ───────────────────────────────────────────
export function resetFilters() {
  const today = new Date();
  const threeDaysAgo = new Date(today);
  threeDaysAgo.setDate(today.getDate() - 3);

  const setVal = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.value = val;
  };

  setVal("filter-news-type",  "");
  setVal("filter-district",   "");
  setVal("filter-date-from",  _formatDate(threeDaysAgo));
  setVal("filter-date-to",    _formatDate(today));

  _state = {
    news_type:  "",
    district:   "",
    date_from:  _formatDate(threeDaysAgo),
    date_to:    _formatDate(today),
  };

  _onFilterChange({ ..._state });
}

// ─── Dışa açık: mevcut filtre durumu ─────────────────────────────────────────
export function getCurrentFilters() {
  return { ..._state };
}

// ─── Yardımcı: <select> doldurmak ────────────────────────────────────────────
function _populateSelect(id, items, placeholder) {
  const el = document.getElementById(id);
  if (!el) return;

  el.innerHTML = `<option value="">${placeholder}</option>`;
  items.forEach((item) => {
    const opt = document.createElement("option");
    opt.value       = item;
    opt.textContent = item;
    el.appendChild(opt);
  });
}

// ─── Yardımcı: tarih formatı YYYY-MM-DD ──────────────────────────────────────
function _formatDate(d) {
  return d.toISOString().split("T")[0];
}

// ─── Haber sayacını güncelle ──────────────────────────────────────────────────
export function updateNewsCount(count) {
  const el = document.getElementById("news-count");
  if (el) el.textContent = count;
}