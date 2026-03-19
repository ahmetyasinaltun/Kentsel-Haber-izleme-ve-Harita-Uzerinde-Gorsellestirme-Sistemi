// Google Maps entegrasyonu
/**
 * map.js — Google Maps entegrasyonu
 * Marker oluşturma, popup (InfoWindow) ve dinamik filtre güncelleme.
 */

// ─── Sabitler ─────────────────────────────────────────────────────────────────
const KOCAELI_CENTER = { lat: 40.7654, lng: 29.9408 };
const DEFAULT_ZOOM   = 11;

// Haber türü → marker rengi + SVG ikonu (Maps inline SVG marker)
const TYPE_CONFIG = {
  "Trafik Kazası": {
    color: "#ef4444",
    bg:    "#1a0a0a",
    emoji: "🚗",
    svg:   _carSVG,
  },
  "Yangın": {
    color: "#f97316",
    bg:    "#1a0d05",
    emoji: "🔥",
    svg:   _fireSVG,
  },
  "Elektrik Kesintisi": {
    color: "#facc15",
    bg:    "#1a1605",
    emoji: "⚡",
    svg:   _boltSVG,
  },
  "Hırsızlık": {
    color: "#a855f7",
    bg:    "#110a1a",
    emoji: "🦹",
    svg:   _theftSVG,
  },
  "Kültürel Etkinlik": {
    color: "#22d3ee",
    bg:    "#051215",
    emoji: "🎭",
    svg:   _cultureSVG,
  },
};

const DEFAULT_CONFIG = { color: "#64748b", bg: "#111827", emoji: "📰", svg: _defaultSVG };

// ─── Modül state ──────────────────────────────────────────────────────────────
let _map          = null;
let _markers      = [];         // { marker, news } çiftleri
let _openWindow   = null;       // Açık InfoWindow
let _newsList     = [];         // Sidebar listesi için referans

// ─── Haritayı başlat (Google Maps geri çağrısından çağrılır) ──────────────────
export function initMap() {
  _map = new google.maps.Map(document.getElementById("map"), {
    center:            KOCAELI_CENTER,
    zoom:              DEFAULT_ZOOM,
    mapId:             "kocaeli_news_map",        // Cloud Console'da oluşturun
    disableDefaultUI:  false,
    zoomControl:       true,
    mapTypeControl:    false,
    streetViewControl: false,
    fullscreenControl: true,
    styles:            _darkMapStyle(),
  });

  // Haritaya tıklanınca açık pencereyi kapat
  _map.addListener("click", () => {
    if (_openWindow) { _openWindow.close(); _openWindow = null; }
    _clearActiveListItem();
  });
}

// ─── Haberleri haritaya yükle ─────────────────────────────────────────────────
export function loadNewsOnMap(newsList) {
  clearMarkers();
  _newsList = newsList;

  newsList.forEach((news, idx) => {
    if (!news.location_coords?.lat || !news.location_coords?.lng) return;

    const cfg     = TYPE_CONFIG[news.news_type] || DEFAULT_CONFIG;
    const marker  = _createMarker(news, cfg);

    marker.addListener("click", () => {
      _openInfoWindow(news, cfg, marker);
      _setActiveListItem(idx);
    });

    _markers.push({ marker, news, idx });
  });

  _renderSidebar(newsList);
}

// ─── Açık InfoWindow ──────────────────────────────────────────────────────────
function _openInfoWindow(news, cfg, marker) {
  if (_openWindow) _openWindow.close();

  const sources = (news.sources || [])
    .map(
      (s) =>
        `<a class="iw-source-link" href="${s.url}" target="_blank" rel="noopener">${s.site_name}</a>`
    )
    .join(" · ");

  const date = news.published_at
    ? new Date(news.published_at).toLocaleDateString("tr-TR", {
        day: "2-digit", month: "long", year: "numeric",
      })
    : "—";

  const primaryUrl = news.sources?.[0]?.url || "#";

  const content = `
    <div class="iw-wrap" style="--cfg-color:${cfg.color};--cfg-bg:${cfg.bg}">
      <div class="iw-type">
        <span class="iw-emoji">${cfg.emoji}</span>
        <span class="iw-type-label">${news.news_type || "Haber"}</span>
      </div>
      <div class="iw-title">${_esc(news.title)}</div>
      <div class="iw-meta">
        <span class="iw-date">📅 ${date}</span>
        ${news.location_text ? `<span class="iw-loc">📍 ${_esc(news.location_text)}</span>` : ""}
      </div>
      ${sources ? `<div class="iw-sources"><span class="iw-src-label">Kaynak:</span> ${sources}</div>` : ""}
      <a class="iw-btn" href="${primaryUrl}" target="_blank" rel="noopener">
        Habere Git →
      </a>
    </div>`;

  _openWindow = new google.maps.InfoWindow({ content, maxWidth: 340 });
  _openWindow.open(_map, marker);
}

// ─── Marker oluştur ───────────────────────────────────────────────────────────
function _createMarker(news, cfg) {
  const pos = { lat: news.location_coords.lat, lng: news.location_coords.lng };

  // AdvancedMarkerElement yoksa fallback
  if (google.maps.marker?.AdvancedMarkerElement) {
    const pin = new google.maps.marker.PinElement({
      glyph:           cfg.emoji,
      background:      cfg.color,
      borderColor:     _lighten(cfg.color, 40),
      glyphColor:      "#fff",
    });
    return new google.maps.marker.AdvancedMarkerElement({
      map:      _map,
      position: pos,
      content:  pin.element,
      title:    news.title,
    });
  }

  // Legacy Marker
  return new google.maps.Marker({
    map:      _map,
    position: pos,
    title:    news.title,
    icon: {
      path:        google.maps.SymbolPath.CIRCLE,
      scale:       10,
      fillColor:   cfg.color,
      fillOpacity: 0.9,
      strokeColor: "#fff",
      strokeWeight: 1.5,
    },
  });
}

// ─── Sidebar haber listesi ────────────────────────────────────────────────────
function _renderSidebar(newsList) {
  const container = document.getElementById("news-list");
  if (!container) return;

  if (!newsList.length) {
    container.innerHTML = `<div class="no-news">Filtrelerle eşleşen haber bulunamadı.</div>`;
    return;
  }

  container.innerHTML = newsList
    .map((n, idx) => {
      const cfg  = TYPE_CONFIG[n.news_type] || DEFAULT_CONFIG;
      const date = n.published_at
        ? new Date(n.published_at).toLocaleDateString("tr-TR", { day: "2-digit", month: "short" })
        : "";
      const hasCoords = n.location_coords?.lat && n.location_coords?.lng;

      return `
        <div class="news-item ${hasCoords ? "has-coords" : "no-coords"}"
             data-idx="${idx}"
             style="--item-color:${cfg.color}"
             role="button" tabindex="0">
          <span class="ni-icon">${cfg.emoji}</span>
          <div class="ni-body">
            <div class="ni-title">${_esc(n.title)}</div>
            <div class="ni-meta">
              ${n.location_text ? `<span>${_esc(n.location_text)}</span>` : ""}
              ${date ? `<span>${date}</span>` : ""}
            </div>
          </div>
        </div>`;
    })
    .join("");

  // Liste öğesine tıkla → haritada marker'ı bul ve aç
  container.querySelectorAll(".news-item.has-coords").forEach((el) => {
    const handler = () => {
      const idx     = parseInt(el.dataset.idx, 10);
      const found   = _markers.find((m) => m.idx === idx);
      if (!found) return;
      _map.panTo(found.marker.position || found.marker.getPosition());
      _map.setZoom(14);
      const cfg = TYPE_CONFIG[found.news.news_type] || DEFAULT_CONFIG;
      _openInfoWindow(found.news, cfg, found.marker);
      _setActiveListItem(idx);
    };
    el.addEventListener("click",   handler);
    el.addEventListener("keydown", (e) => { if (e.key === "Enter") handler(); });
  });
}

// ─── Aktif liste öğesi ────────────────────────────────────────────────────────
function _setActiveListItem(idx) {
  document.querySelectorAll(".news-item").forEach((el) => el.classList.remove("active"));
  const el = document.querySelector(`.news-item[data-idx="${idx}"]`);
  if (el) {
    el.classList.add("active");
    el.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
}

function _clearActiveListItem() {
  document.querySelectorAll(".news-item").forEach((el) => el.classList.remove("active"));
}

// ─── Tüm marker'ları kaldır ───────────────────────────────────────────────────
export function clearMarkers() {
  _markers.forEach(({ marker }) => {
    if (marker.map !== undefined) marker.map = null;          // AdvancedMarker
    else if (marker.setMap)       marker.setMap(null);        // Legacy
  });
  _markers = [];
  if (_openWindow) { _openWindow.close(); _openWindow = null; }
}

// ─── Konum görünümüne odaklan ─────────────────────────────────────────────────
export function focusKocaeli() {
  if (_map) {
    _map.panTo(KOCAELI_CENTER);
    _map.setZoom(DEFAULT_ZOOM);
  }
}

// ─── Yardımcı: HTML escape ────────────────────────────────────────────────────
function _esc(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ─── Yardımcı: rengi aydınlat (basit hex manipülasyon) ───────────────────────
function _lighten(hex, amt) {
  const num = parseInt(hex.replace("#", ""), 16);
  const r   = Math.min(255, (num >> 16) + amt);
  const g   = Math.min(255, ((num >> 8) & 0xff) + amt);
  const b   = Math.min(255, (num & 0xff) + amt);
  return "#" + [r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("");
}

// ─── SVG ikon stub'ları (Google inline SVG gerekirse buraya) ──────────────────
function _carSVG()     { return null; }
function _fireSVG()    { return null; }
function _boltSVG()    { return null; }
function _theftSVG()   { return null; }
function _cultureSVG() { return null; }
function _defaultSVG() { return null; }

// ─── Koyu harita stili ────────────────────────────────────────────────────────
function _darkMapStyle() {
  return [
    { elementType: "geometry",                           stylers: [{ color: "#0d1117" }] },
    { elementType: "labels.text.stroke",                 stylers: [{ color: "#0d1117" }] },
    { elementType: "labels.text.fill",                   stylers: [{ color: "#4a6280" }] },
    { featureType: "administrative",    elementType: "geometry.stroke", stylers: [{ color: "#1e2d45" }] },
    { featureType: "administrative.land_parcel", elementType: "labels.text.fill", stylers: [{ color: "#2a3f5a" }] },
    { featureType: "poi",               elementType: "geometry",        stylers: [{ color: "#111827" }] },
    { featureType: "poi",               elementType: "labels.text.fill",stylers: [{ color: "#374a60" }] },
    { featureType: "poi.park",          elementType: "geometry",        stylers: [{ color: "#0a1a10" }] },
    { featureType: "poi.park",          elementType: "labels.text.fill",stylers: [{ color: "#1a4028" }] },
    { featureType: "road",              elementType: "geometry",        stylers: [{ color: "#1a2535" }] },
    { featureType: "road",              elementType: "geometry.stroke", stylers: [{ color: "#101820" }] },
    { featureType: "road",              elementType: "labels.text.fill",stylers: [{ color: "#3a5070" }] },
    { featureType: "road.highway",      elementType: "geometry",        stylers: [{ color: "#1e3048" }] },
    { featureType: "road.highway",      elementType: "geometry.stroke", stylers: [{ color: "#0e1e30" }] },
    { featureType: "road.highway",      elementType: "labels.text.fill",stylers: [{ color: "#2a6090" }] },
    { featureType: "transit",           elementType: "geometry",        stylers: [{ color: "#0e1a28" }] },
    { featureType: "transit.station",   elementType: "labels.text.fill",stylers: [{ color: "#2a4a6a" }] },
    { featureType: "water",             elementType: "geometry",        stylers: [{ color: "#060e18" }] },
    { featureType: "water",             elementType: "labels.text.fill",stylers: [{ color: "#1a3040" }] },
  ];
}

// ─── Global callback (Google Maps async loader için) ─────────────────────────
window.__mapReady = initMap;