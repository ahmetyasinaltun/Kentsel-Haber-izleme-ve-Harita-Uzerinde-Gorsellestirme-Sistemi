/**
 * map.js — Google Maps entegrasyonu
 *
 * ÖNEMLİ: AdvancedMarkerElement KULLANILMIYOR (Map ID gerektirir).
 * Legacy google.maps.Marker + custom SVG icon kullanılıyor.
 * YENİ: MarkerClusterer, Event Delegation ve Bellek Yönetimi eklendi.
 */

// ─── Kocaeli ve Komşuları İçin Güncellenmiş Koordinatlar ──────────────────────
const KOCAELI_CENTER = { lat: 40.8532, lng: 29.8815 }; 
const DEFAULT_ZOOM   = 12;   // İzmit merkezi net görecek seviye

const TYPE_CONFIG = {
  "Trafik Kazası":      { color: "#ef4444", emoji: "🚗" },
  "Yangın":             { color: "#f97316", emoji: "🔥" },
  "Elektrik Kesintisi": { color: "#facc15", emoji: "⚡" },
  "Hırsızlık":          { color: "#a855f7", emoji: "🦹" },
  "Kültürel Etkinlik":  { color: "#22d3ee", emoji: "🎭" },
};
const DEFAULT_CONFIG = { color: "#64748b", emoji: "📰" };

let _map           = null;
let _markers       = [];
let _openWindow    = null;
let _theme         = "dark";
let _markerCluster = null; // Clusterer için global değişken

// ─── Kocaeli ve komşularını kapsayan genişletilmiş kısıtlama ──────────────────
const BOUNDS = {
  latLngBounds: {
    north: 41.30,   // Kefken / Karadeniz açıkları
    south: 40.40,   // Karamürsel güneyi / İznik sınırları
    west:  29.25,   // Gebze / İstanbul Tuzla sınırı
    east:  30.60,   // Sakarya / Adapazarı sınırı
  },
  strictBounds: true,
};

// ─── Haritayı başlat ──────────────────────────────────────────────────────────
export function initMap(theme = "dark") {
  _theme = theme;
  _map = new google.maps.Map(document.getElementById("map"), {
    center:            KOCAELI_CENTER,
    zoom:              DEFAULT_ZOOM,
    minZoom:           8,    // Tüm Kocaeli ili görünecek seviye
    maxZoom:           18,
    restriction:       BOUNDS,
    disableDefaultUI:  false,
    zoomControl:       true,
    mapTypeControl:    false,
    streetViewControl: false,
    fullscreenControl: true,
    styles:            theme === "light" ? _lightStyle() : _darkStyle(),
  });

  _map.addListener("click", () => {
    if (_openWindow) { _openWindow.close(); _openWindow = null; }
    _clearActive();
  });
}

// ─── Tema uygula ─────────────────────────────────────────────────────────────
export function setMapTheme(theme) {
  _theme = theme;
  if (_map) _map.setOptions({ styles: theme === "light" ? _lightStyle() : _darkStyle() });
}

// ─── Haberleri haritaya yükle ve Kümele (Cluster) ─────────────────────────────
export function loadNewsOnMap(newsList) {
  clearMarkers();
  if (!newsList.length) { _renderSidebar([]); return; }

  const googleMarkers = []; // Clusterer'a geçilecek ham marker dizisi

  newsList.forEach((news, idx) => {
    if (!news.location_coords?.lat || !news.location_coords?.lng) return;

    const cfg    = TYPE_CONFIG[news.news_type] || DEFAULT_CONFIG;
    const marker = _createMarker(news, cfg);

    marker.addListener("click", () => {
      _openInfoWindow(news, cfg, marker);
      _setActive(idx);
    });

    _markers.push({ marker, news, idx });
    googleMarkers.push(marker);
  });

  // Marker Clusterer'ı başlat (Harita uzaklaştıkça marker'ları gruplar)
  if (typeof markerClusterer !== 'undefined') {
    _markerCluster = new markerClusterer.MarkerClusterer({ 
        map: _map, 
        markers: googleMarkers 
    });
  } else {
    console.warn("MarkerClusterer kütüphanesi bulunamadı. Lütfen HTML dosyanıza ekleyin.");
  }

  _renderSidebar(newsList);
}

// ─── InfoWindow ───────────────────────────────────────────────────────────────
function _openInfoWindow(news, cfg, marker) {
  if (_openWindow) _openWindow.close();

  const sources = (news.sources || [])
    .map(s => `<a class="iw-source-link" href="${s.url}" target="_blank" rel="noopener">${s.site_name}</a>`)
    .join(" · ");

  const date = news.published_at
    ? new Date(news.published_at).toLocaleDateString("tr-TR", {
        day: "2-digit", month: "long", year: "numeric",
      })
    : "—";

  const primaryUrl = news.sources?.[0]?.url || "#";

  const html = `
    <div class="iw-wrap" style="--cfg-color:${cfg.color}">
      <div class="iw-type">
        <span class="iw-emoji">${cfg.emoji}</span>
        <span class="iw-type-label">${news.news_type || "Haber"}</span>
      </div>
      <div class="iw-title">${_esc(news.title)}</div>
      <div class="iw-meta">
        <span>📅 ${date}</span>
        ${news.location_text ? `<span>📍 ${_esc(news.location_text)}</span>` : ""}
      </div>
      ${sources ? `<div class="iw-sources"><span class="iw-src-label">Kaynak:</span> ${sources}</div>` : ""}
      <a class="iw-btn" href="${primaryUrl}" target="_blank" rel="noopener">Habere Git →</a>
    </div>`;

  _openWindow = new google.maps.InfoWindow({ content: html, maxWidth: 340 });
  _openWindow.open(_map, marker);
}

// ─── SVG Marker ───────────────────────────────────────────────────────────────
function _createMarker(news, cfg) {
  const pos = { lat: news.location_coords.lat, lng: news.location_coords.lng };

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40">
    <circle cx="20" cy="20" r="17" fill="${cfg.color}" stroke="white" stroke-width="2.5" opacity="0.92"/>
    <text x="20" y="26" text-anchor="middle" font-size="17" font-family="serif">${cfg.emoji}</text>
  </svg>`;

  return new google.maps.Marker({
    map:      _map,
    position: pos,
    title:    news.title,
    icon: {
      url:        "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(svg),
      scaledSize: new google.maps.Size(40, 40),
      anchor:     new google.maps.Point(20, 20),
    },
    optimized: false,
  });
}

// ─── Sidebar listesi (Event Delegation ile optimize edildi) ───────────────────
function _renderSidebar(newsList) {
  const container = document.getElementById("news-list");
  if (!container) return;

  if (!newsList.length) {
    container.innerHTML = `<div class="no-news">Filtrelerle eşleşen haber bulunamadı.</div>`;
    // Önceki event listener'ları temizlemek için onClick'i sıfırlıyoruz
    container.onclick = null;
    container.onkeydown = null;
    return;
  }

  container.innerHTML = newsList.map((n, idx) => {
    const cfg      = TYPE_CONFIG[n.news_type] || DEFAULT_CONFIG;
    const date     = n.published_at
      ? new Date(n.published_at).toLocaleDateString("tr-TR", { day: "2-digit", month: "short" })
      : "";
    const hasCoords = !!(n.location_coords?.lat && n.location_coords?.lng);

    return `
      <div class="news-item ${hasCoords ? "has-coords" : "no-coords"}"
           data-idx="${idx}" style="--item-color:${cfg.color}"
           role="button" tabindex="0">
        <span class="ni-icon">${cfg.emoji}</span>
        <div class="ni-body">
          <div class="ni-title">${_esc(n.title)}</div>
          <div class="ni-meta">
            ${n.location_text ? `<span>${_esc(n.location_text)}</span>` : ""}
            ${date            ? `<span>${date}</span>` : ""}
          </div>
        </div>
      </div>`;
  }).join("");

  // Event Delegation: Tüm öğelere ayrı ayrı dinleyici eklemek yerine 
  // ana kapsayıcı üzerinden tıklamaları yakalıyoruz. (Performans Optimizasyonu)
  const handleItemInteraction = (target) => {
    const el = target.closest(".news-item.has-coords");
    if (!el) return;

    const idx   = parseInt(el.dataset.idx, 10);
    const found = _markers.find(m => m.idx === idx);
    if (!found) return;

    // Haritayı hareket ettir ve InfoWindow aç
    _map.panTo(found.marker.getPosition());
    _map.setZoom(15);
    _openInfoWindow(found.news, TYPE_CONFIG[found.news.news_type] || DEFAULT_CONFIG, found.marker);
    _setActive(idx);
  };

  container.onclick = (e) => handleItemInteraction(e.target);
  
  container.onkeydown = (e) => { 
    if (e.key === "Enter") handleItemInteraction(e.target); 
  };
}

// ─── Aktif öğe ───────────────────────────────────────────────────────────────
function _setActive(idx) {
  document.querySelectorAll(".news-item").forEach(el => el.classList.remove("active"));
  const el = document.querySelector(`.news-item[data-idx="${idx}"]`);
  if (el) { el.classList.add("active"); el.scrollIntoView({ behavior: "smooth", block: "nearest" }); }
}
function _clearActive() {
  document.querySelectorAll(".news-item").forEach(el => el.classList.remove("active"));
}

// ─── Markerleri ve Dinleyicileri temizle (Bellek Yönetimi) ────────────────────
export function clearMarkers() {
  // Clusterer varsa temizle
  if (_markerCluster) {
    _markerCluster.clearMarkers();
  }

  // Bellek sızıntılarını (memory leak) önlemek için event listener'ları temizle
  _markers.forEach(({ marker }) => {
    google.maps.event.clearInstanceListeners(marker);
    marker.setMap(null);
  });
  
  _markers = [];
  
  if (_openWindow) { 
    _openWindow.close(); 
    _openWindow = null; 
  }
}

// ─── HTML escape ─────────────────────────────────────────────────────────────
function _esc(s) {
  return String(s || "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// ════════════════════════════════════════════════════
// HARİTA STİLLERİ — POI + transit tamamen gizli
// ════════════════════════════════════════════════════

function _darkStyle() {
  return [
    { elementType: "geometry",               stylers: [{ color: "#0d1117" }] },
    { elementType: "labels.text.stroke",     stylers: [{ color: "#0d1117" }] },
    { elementType: "labels.text.fill",       stylers: [{ color: "#4a6280" }] },
    { featureType: "administrative",         elementType: "geometry.stroke",   stylers: [{ color: "#1e2d45" }] },
    { featureType: "administrative.locality",elementType: "labels.text.fill",  stylers: [{ color: "#3a5070" }] },
    { featureType: "administrative.province",elementType: "geometry.stroke",   stylers: [{ color: "#00d4ff" }, { weight: 1.5 }] },
    { featureType: "poi",                    stylers: [{ visibility: "off" }] },
    { featureType: "poi.park", elementType: "geometry",  stylers: [{ color: "#0a1a10" }] },
    { featureType: "poi.park", elementType: "labels",    stylers: [{ visibility: "off" }] },
    { featureType: "transit",  elementType: "labels.icon",  stylers: [{ visibility: "off" }] },
    { featureType: "transit",  elementType: "geometry",     stylers: [{ color: "#0e1a28" }] },
    { featureType: "transit.station", elementType: "labels.text.fill", stylers: [{ color: "#2a4a6a" }] },
    { featureType: "road",         elementType: "geometry",         stylers: [{ color: "#1a2535" }] },
    { featureType: "road",         elementType: "geometry.stroke",  stylers: [{ color: "#101820" }] },
    { featureType: "road",         elementType: "labels.text.fill", stylers: [{ color: "#3a5070" }] },
    { featureType: "road.highway", elementType: "geometry",         stylers: [{ color: "#1e3048" }] },
    { featureType: "road.highway", elementType: "geometry.stroke",  stylers: [{ color: "#0e1e30" }] },
    { featureType: "road.highway", elementType: "labels.text.fill", stylers: [{ color: "#2a6090" }] },
    { featureType: "water", elementType: "geometry",         stylers: [{ color: "#060e18" }] },
    { featureType: "water", elementType: "labels.text.fill", stylers: [{ color: "#1a3040" }] },
  ];
}

function _lightStyle() {
  return [
    { elementType: "geometry",               stylers: [{ color: "#f5f7fa" }] },
    { elementType: "labels.text.stroke",     stylers: [{ color: "#f5f7fa" }] },
    { elementType: "labels.text.fill",       stylers: [{ color: "#7a8fa8" }] },
    { featureType: "administrative",         elementType: "geometry.stroke",   stylers: [{ color: "#c8d6e8" }] },
    { featureType: "administrative.locality",elementType: "labels.text.fill",  stylers: [{ color: "#3a5070" }] },
    { featureType: "administrative.province",elementType: "geometry.stroke",   stylers: [{ color: "#0066cc" }, { weight: 1.5 }] },
    { featureType: "poi",                    stylers: [{ visibility: "off" }] },
    { featureType: "poi.park", elementType: "geometry", stylers: [{ color: "#d8edd4" }] },
    { featureType: "poi.park", elementType: "labels",   stylers: [{ visibility: "off" }] },
    { featureType: "transit",  elementType: "labels.icon",  stylers: [{ visibility: "off" }] },
    { featureType: "transit",  elementType: "geometry",     stylers: [{ color: "#e2e8f0" }] },
    { featureType: "transit.station", elementType: "labels.text.fill", stylers: [{ color: "#8fa3bc" }] },
    { featureType: "road",         elementType: "geometry",         stylers: [{ color: "#ffffff" }] },
    { featureType: "road",         elementType: "geometry.stroke",  stylers: [{ color: "#dde4ee" }] },
    { featureType: "road",         elementType: "labels.text.fill", stylers: [{ color: "#7a8fa8" }] },
    { featureType: "road.highway", elementType: "geometry",         stylers: [{ color: "#fde9c0" }] },
    { featureType: "road.highway", elementType: "geometry.stroke",  stylers: [{ color: "#f5d590" }] },
    { featureType: "road.highway", elementType: "labels.text.fill", stylers: [{ color: "#6b7a8d" }] },
    { featureType: "water", elementType: "geometry",         stylers: [{ color: "#b8d4e8" }] },
    { featureType: "water", elementType: "labels.text.fill", stylers: [{ color: "#6a8aaa" }] },
  ];
}