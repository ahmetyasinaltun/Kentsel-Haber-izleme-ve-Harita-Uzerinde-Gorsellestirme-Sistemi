// Backend ile iletişim
/**
 * api.js — Backend iletişim katmanı
 * Tüm fetch çağrıları burada merkezi olarak yönetilir.
 */

const API_BASE = "http://localhost:8000/api";

// ─── Yardımcı: İstek gönder ─────────────────────────────────────────────────
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

// ─── Haberleri getir ─────────────────────────────────────────────────────────
/**
 * Filtrelere göre haber listesi döner.
 * @param {Object} filters - { news_type, district, date_from, date_to }
 * @returns {Promise<Array>}
 */
// api.js — fetchNews fonksiyonunu şöyle değiştir:

export async function fetchNews(filters = {}) {
  const params = new URLSearchParams();
  if (filters.news_type)  params.set("news_type",  filters.news_type);
  if (filters.district)   params.set("district",   filters.district);
  if (filters.date_from)  params.set("start_date", filters.date_from);  // ← backend "start_date" bekliyor
  if (filters.date_to)    params.set("end_date",   filters.date_to);    // ← backend "end_date" bekliyor

  const qs = params.toString();
  const data = await request(`/news${qs ? "?" + qs : ""}`);
  return data.news ?? [];   // ← { count, news: [...] } yerine direkt array döner
}

// ─── Filtre seçeneklerini getir ──────────────────────────────────────────────
/**
 * Haber türleri ve ilçe listesini döner.
 * @returns {Promise<{ news_types: string[], districts: string[] }>}
 */
export async function fetchFilterOptions() {
  return request("/filter/options");
}

// ─── Scraping tetikle ────────────────────────────────────────────────────────
/**
 * Sunucu tarafında yeni scraping başlatır.
 * @returns {Promise<{ message: string, scraped: number, saved: number }>}
 */
export async function triggerScrape() {
  return request("/scrape", { method: "POST" });
}

// ─── Tek haber getir ─────────────────────────────────────────────────────────
/**
 * Belirli bir haberin detayını döner.
 * @param {string} id - MongoDB ObjectId string
 * @returns {Promise<Object>}
 */
export async function fetchNewsById(id) {
  return request(`/news/${id}`);
}