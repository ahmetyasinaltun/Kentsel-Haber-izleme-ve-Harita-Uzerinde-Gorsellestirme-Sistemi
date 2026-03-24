/**
 * api.js — Backend iletişim katmanı
 */

const API_BASE = "http://localhost:8000/api";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/** Filtrelere göre haberler — backend tarihe göre azalan sırada döner */
export async function fetchNews(filters = {}) {
  const p = new URLSearchParams();
  if (filters.news_type) p.set("news_type",  filters.news_type);
  if (filters.district)  p.set("district",   filters.district);
  if (filters.date_from) p.set("start_date", filters.date_from);
  if (filters.date_to)   p.set("end_date",   filters.date_to);
  const qs   = p.toString();
  const data = await request(`/news${qs ? "?" + qs : ""}`);
  return data.news ?? [];
}

/** Tüm haberleri MongoDB'den sil (geocache korunur) */
export async function deleteAllNews() {
  return request("/news", { method: "DELETE" });
}

/** Haber türleri ve ilçe listesi */
export async function fetchFilterOptions() {
  return request("/filter/options");
}

/** Scraping başlat (arka planda çalışır) */
export async function triggerScrape() {
  return request("/scrape", { method: "POST" });
}

/** Tek haber detayı */
export async function fetchNewsById(id) {
  return request(`/news/${id}`);
}