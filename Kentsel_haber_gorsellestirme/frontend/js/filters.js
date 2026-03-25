/**
 * filters.js — Filtre paneli mantığı
 *
 * - Filtre değişikliklerinde otomatik yükleme YAPILMAZ.
 * - setFilterNewsType() legend chip'lerinin state'i senkronize etmesi için export edildi.
 */

import { fetchFilterOptions } from "./api.js";

let _state = {
  news_type: "",
  district:  "",
  date_from: "",
  date_to:   "",
};

let _onDateChange = null; // Tarih değişince çağrılacak callback

// ─── Dışa açık: tarih değişim callback'i kaydet ──────────────────────────────
export function onDateChange(fn) {
  _onDateChange = fn;
}

// ─── İlklendirme ─────────────────────────────────────────────────────────────
export async function initFilters() {
  const today        = new Date();
  const threeDaysAgo = new Date(today);
  threeDaysAgo.setDate(today.getDate() - 3);

  const fromEl = document.getElementById("filter-date-from");
  const toEl   = document.getElementById("filter-date-to");

  if (fromEl) fromEl.value = _fmt(threeDaysAgo);
  if (toEl)   toEl.value   = _fmt(today);

  _state.date_from = fromEl?.value || "";
  _state.date_to   = toEl?.value   || "";

  try {
    const opts = await fetchFilterOptions();
    _fill("filter-news-type", opts.news_types || [], "Tüm Türler");
    _fill("filter-district",  opts.districts  || [], "Tüm İlçeler");
  } catch(e) {
    console.warn("Filtre seçenekleri yüklenemedi:", e.message);
    _fill("filter-news-type", [
      "Trafik Kazası","Yangın","Elektrik Kesintisi","Hırsızlık","Kültürel Etkinlik",
    ], "Tüm Türler");
  }

  _bindEvents();
}

// ─── Event bağlama ────────────────────────────────────────────────────────────
function _bindEvents() {
  ["filter-news-type","filter-district"].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener("change", _syncState);
  });

  // Tarih filtreleri değişince state güncelle + callback tetikle
  ["filter-date-from","filter-date-to"].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener("change", () => {
      _syncState();
      if (_onDateChange) _onDateChange();
    });
  });
}

function _syncState() {
  _state.news_type = document.getElementById("filter-news-type")?.value || "";
  _state.district  = document.getElementById("filter-district")?.value  || "";
  _state.date_from = document.getElementById("filter-date-from")?.value || "";
  _state.date_to   = document.getElementById("filter-date-to")?.value   || "";
}

// ─── Dışa açık: filtreleri sıfırla ───────────────────────────────────────────
export function resetFilters() {
  const today        = new Date();
  const threeDaysAgo = new Date(today);
  threeDaysAgo.setDate(today.getDate() - 3);

  const set = (id, v) => { const el = document.getElementById(id); if (el) el.value = v; };
  set("filter-news-type",  "");
  set("filter-district",   "");
  set("filter-date-from",  _fmt(threeDaysAgo));
  set("filter-date-to",    _fmt(today));

  _state = { news_type:"", district:"", date_from:_fmt(threeDaysAgo), date_to:_fmt(today) };
}

// ─── Dışa açık: news_type state'ini doğrudan güncelle ────────────────────────
// Legend chip'leri select DOM değerini zaten değiştiriyor;
// bu fonksiyon filters.js modül state'ini de senkronize eder.
export function setFilterNewsType(value) {
  _state.news_type = value || "";
}

// ─── Dışa açık: mevcut filtreler ─────────────────────────────────────────────
export function getCurrentFilters() {
  return { ..._state };
}

// ─── Dışa açık: haber sayacını güncelle ──────────────────────────────────────
export function updateNewsCount(count) {
  const el = document.getElementById("news-count");
  if (el) el.textContent = count;
}

// ─── Yardımcı: <select> doldur ───────────────────────────────────────────────
function _fill(id, items, placeholder) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = `<option value="">${placeholder}</option>`;
  items.forEach(item => {
    const o = document.createElement("option");
    o.value = item; o.textContent = item;
    el.appendChild(o);
  });
}

// ─── Yardımcı: YYYY-MM-DD ────────────────────────────────────────────────────
function _fmt(d) { return d.toISOString().split("T")[0]; }