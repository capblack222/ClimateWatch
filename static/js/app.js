// ── State ──────────────────────────────────────────────────────────────────
let currentCity = null;  // { city, country, country_code, lat, lon }
let debounceTimer = null;

// ── DOM refs ───────────────────────────────────────────────────────────────
const citySearch    = document.getElementById("citySearch");
const searchResults = document.getElementById("searchResults");
const savedList     = document.getElementById("savedList");
const dashboard     = document.getElementById("dashboard");
const landingState  = document.getElementById("landingState");
const loadingState  = document.getElementById("loadingState");
const saveBtn       = document.getElementById("saveBtn");
const resumeBtn     = document.getElementById("resumeBtn");

// ── Search ─────────────────────────────────────────────────────────────────
citySearch.addEventListener("input", () => {
  clearTimeout(debounceTimer);
  const q = citySearch.value.trim();
  if (q.length < 2) { 
    searchResults.classList.add("hidden"); 
    return; 
  }
  debounceTimer = setTimeout(() => doSearch(q), 350);
});

citySearch.addEventListener("keydown", e => {
  if (e.key === "Escape") searchResults.classList.add("hidden");
});

document.addEventListener("click", e => {
  if (!e.target.closest(".search-block")) searchResults.classList.add("hidden");
});

async function doSearch(q) {
  const resp = await fetch(`/search?q=${encodeURIComponent(q)}`);
  const results = await resp.json();
  searchResults.innerHTML = "";
  if (!results.length) {
    searchResults.innerHTML = `<li style="color:var(--muted);cursor:default">No results found</li>`;
  } else {
    results.forEach(r => {
      const li = document.createElement("li");
      const sub = [r.admin1, r.country].filter(Boolean).join(", ");
      li.innerHTML = `<div class="result-city">${r.name}</div><div class="result-sub">${sub}</div>`;
      li.addEventListener("click", () => {
        searchResults.classList.add("hidden");
        citySearch.value = "";
        loadWeather({ city: r.name, country: r.country, country_code: r.country_code, lat: r.latitude, lon: r.longitude });
      });
      searchResults.appendChild(li);
    });
  }
  searchResults.classList.remove("hidden");
}

// ── Weather Load ───────────────────────────────────────────────────────────
async function loadWeather({ city, country, country_code, lat, lon }) {
  currentCity = { city, country, country_code, lat, lon };

  showLoading();

  const params = new URLSearchParams({ lat, lon, city, country, country_code });
  const resp = await fetch(`/weather?${params}`);
  if (!resp.ok) { 
    alert("Failed to load weather."); 
    showLanding(); 
    return; 
  }
  const data = await resp.json();

  renderDashboard(data);
}

function showLoading() {
  landingState.classList.add("hidden");
  dashboard.classList.add("hidden");
  loadingState.classList.remove("hidden");
}
function showLanding() {
  landingState.classList.remove("hidden");
  dashboard.classList.add("hidden");
  loadingState.classList.add("hidden");
}

// ── Render ─────────────────────────────────────────────────────────────────
function renderDashboard(data) {
  loadingState.classList.add("hidden");

  document.getElementById("cityTitle").textContent    = data.city;
  document.getElementById("countryLabel").textContent  = data.country;
  document.getElementById("currentEmoji").textContent  = data.current.emoji;
  document.getElementById("currentTemp").textContent   = `${Math.round(data.current.temperature ?? 0)}°C`;
  document.getElementById("currentDesc").textContent   = data.current.description;
  document.getElementById("humidity").textContent      = data.current.humidity ?? "—";
  document.getElementById("precipitation").textContent = data.current.precipitation ?? "0";
  document.getElementById("windSpeed").textContent     = Math.round(data.current.wind_speed ?? 0);
  document.getElementById("feelsLike").textContent     = Math.round(data.current.feels_like ?? 0);

  // Activity suggestion
  document.getElementById("suggestionIcon").textContent = data.suggestion.icon;
  document.getElementById("suggestionText").textContent = data.suggestion.text;
  document.getElementById("suggestionNote").textContent = data.suggestion.note || "";

  // Climate indicators
  renderClimate(data.climate);

  // Forecast
  renderForecast(data.forecast);

  // Save button state
  checkIfSaved();

  dashboard.classList.remove("hidden");
  dashboard.classList.add("hidden"); // re-trigger animation
  void dashboard.offsetWidth;
  dashboard.classList.remove("hidden");
}

function renderClimate(climate) {
  const container = document.getElementById("climateContent");
  const keys = Object.keys(climate);
  if (!keys.length) {
    container.innerHTML = `<div class="climate-placeholder">No indicators available for this country.</div>`;
    return;
  }
  container.innerHTML = keys.slice(0, 3).map(key => {
    const item = climate[key];
    const label = key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
    const pct = key.includes("co2") ? Math.min((item.value / 20) * 100, 100) : Math.min(item.value * 2, 100);
    return `
      <div class="climate-item">
        <div class="climate-name">${label}</div>
        <div class="climate-val">${item.value} <span style="font-size:0.8rem;font-family:'DM Sans'">${item.unit}</span></div>
        <div class="climate-meta">Data year: ${item.year}</div>
        <div class="climate-bar-wrap"><div class="climate-bar" style="width:${pct}%"></div></div>
      </div>
    `;
  }).join("");
}

function renderForecast(forecast) {
  const row = document.getElementById("forecastRow");
  row.innerHTML = forecast.map(day => {
    const date = new Date(day.date);
    const label = date.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
    return `
      <div class="forecast-day">
        <div class="fc-date">${label}</div>
        <span class="fc-emoji">${day.emoji}</span>
        <div class="fc-desc">${day.description}</div>
        <div class="fc-temps">
          <span class="fc-max">${Math.round(day.temp_max)}°</span>
          <span class="fc-min">${Math.round(day.temp_min)}°</span>
        </div>
        <div class="fc-precip">${day.precip > 0 ? day.precip + " mm" : ""}</div>
      </div>
    `;
  }).join("");
}

// ── Save / Unsave ──────────────────────────────────────────────────────────
saveBtn.addEventListener("click", async () => {
  if (!currentCity) return;
  const isCurrentlySaved = saveBtn.classList.contains("saved");

  if (isCurrentlySaved) {
    // Find id from saved list
    const item = [...document.querySelectorAll(".saved-item")].find(
      el => el.dataset.city === currentCity.city
    );
    if (item) await doUnsave(item.dataset.id, item);
  } else {
    await doSave(currentCity);
  }
});

async function doSave({ city, country, country_code, lat, lon }) {
  const resp = await fetch("/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ city, country, country_code, lat, lon })
  });
  const data = await resp.json();
  if (data.status === "saved") {
    saveBtn.classList.add("saved");
    saveBtn.textContent = "★ Saved";
    refreshSavedList();
  }
}

async function doUnsave(id, el) {
  await fetch("/unsave", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: parseInt(id) })
  });
  el.remove();
  checkEmptySaved();
  saveBtn.classList.remove("saved");
  saveBtn.textContent = "☆ Save Location";
}

async function checkIfSaved() {
  saveBtn.classList.remove("saved");
  saveBtn.textContent = "☆ Save Location";
  const items = document.querySelectorAll(".saved-item");
  for (const item of items) {
    if (item.dataset.city === currentCity?.city) {
      saveBtn.classList.add("saved");
      saveBtn.textContent = "★ Saved";
      break;
    }
  }
}

async function refreshSavedList() {
  const resp = await fetch("/saved");
  const locations = await resp.json();
  savedList.innerHTML = "";
  if (!locations.length) {
    savedList.innerHTML = `<li class="empty-saved" id="emptySaved">No saved locations yet.</li>`;
    return;
  }
  locations.forEach(loc => {
    const li = document.createElement("li");
    li.className = "saved-item";
    li.dataset.id = loc.id;
    li.dataset.lat = loc.latitude;
    li.dataset.lon = loc.longitude;
    li.dataset.city = loc.city_name;
    li.dataset.country = loc.country_name;
    li.dataset.cc = loc.country_code;
    li.innerHTML = `
      <span class="saved-city">${loc.city_name}</span>
      <span class="saved-country">${loc.country_name}</span>
      <button class="remove-btn" title="Remove">✕</button>
    `;
    attachSavedItemEvents(li);
    savedList.appendChild(li);
  });
}

function attachSavedItemEvents(li) {
  li.addEventListener("click", e => {
    if (e.target.classList.contains("remove-btn")) return;
    loadWeather({
      city: li.dataset.city,
      country: li.dataset.country,
      country_code: li.dataset.cc,
      lat: parseFloat(li.dataset.lat),
      lon: parseFloat(li.dataset.lon)
    });
  });
  li.querySelector(".remove-btn").addEventListener("click", async e => {
    e.stopPropagation();
    await doUnsave(li.dataset.id, li);
  });
}

function checkEmptySaved() {
  if (!savedList.querySelector(".saved-item")) {
    savedList.innerHTML = `<li class="empty-saved">No saved locations yet.</li>`;
  }
}

// ── Existing saved items ───────────────────────────────────────────────────
document.querySelectorAll(".saved-item").forEach(li => attachSavedItemEvents(li));

// ── Resume last session ────────────────────────────────────────────────────
if (resumeBtn) {
  resumeBtn.addEventListener("click", () => {
    loadWeather({
      city: resumeBtn.dataset.city,
      country: resumeBtn.dataset.country,
      country_code: resumeBtn.dataset.cc,
      lat: parseFloat(resumeBtn.dataset.lat),
      lon: parseFloat(resumeBtn.dataset.lon)
    });
  });
}
