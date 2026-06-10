/* ================================================================
   Charles Hartmann — App Portfolio
   Client-side catalog renderer
   ================================================================ */

"use strict";

const BUYMEACOFFEE = "https://buymeacoffee.com/charleshartmann";
const GITHUB_PROFILE = "https://github.com/chartmann1590";

// Category display config
const CAT_META = {
  android: { icon: "📱", label: "Android" },
  web:     { icon: "🌐", label: "Web" },
  ai:      { icon: "🤖", label: "AI Tool" },
  python:  { icon: "🐍", label: "Python" },
  game:    { icon: "🎮", label: "Game" },
  iot:     { icon: "🔧", label: "IoT" },
  other:   { icon: "⚙️",  label: "Other" },
};

// Icon background gradients (hashed by name)
const ICON_GRADIENTS = [
  ["#4f6fff", "#a855f7"],
  ["#22d3ee", "#4f6fff"],
  ["#f472b6", "#9333ea"],
  ["#34d399", "#0891b2"],
  ["#fbbf24", "#f97316"],
  ["#a78bfa", "#6d28d9"],
  ["#f87171", "#e11d48"],
  ["#60a5fa", "#1d4ed8"],
  ["#4ade80", "#16a34a"],
  ["#fb923c", "#dc2626"],
];

function iconGradient(name) {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = (hash * 31 + name.charCodeAt(i)) | 0;
  }
  return ICON_GRADIENTS[Math.abs(hash) % ICON_GRADIENTS.length];
}

function langClass(lang) {
  if (!lang) return "lang-default";
  const map = {
    Kotlin: "lang-kotlin",
    Java: "lang-java",
    Python: "lang-python",
    JavaScript: "lang-javascript",
    TypeScript: "lang-typescript",
    HTML: "lang-html",
    CSS: "lang-css",
    C: "lang-c",
  };
  return map[lang] || "lang-default";
}

function timeAgo(dateStr) {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const days = Math.floor(diff / 86400000);
  if (days === 0) return "today";
  if (days === 1) return "yesterday";
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months}mo ago`;
  return `${Math.floor(months / 12)}y ago`;
}

function hasGooglePlay(repo) {
  const topics = repo.topics || [];
  return topics.some(t => ["google-play", "play-store", "playstore", "android-app"].includes(t));
}

function createCard(repo, index) {
  const [g1, g2] = iconGradient(repo.name);
  const letter = repo.name.charAt(0).toUpperCase();
  const cat = CAT_META[repo.category] || CAT_META.other;
  const slug = repo.name.toLowerCase().replace(/[_\s]/g, "-");

  const starsHtml = repo.stars > 0
    ? `<span class="stat-item">⭐ ${repo.stars}</span>` : "";
  const forksHtml = repo.forks > 0
    ? `<span class="stat-item">🍴 ${repo.forks}</span>` : "";
  const updatedHtml = repo.pushed_at
    ? `<span class="stat-item" title="${repo.pushed_at}">${timeAgo(repo.pushed_at)}</span>` : "";

  const demoLink = repo.homepage
    ? `<a href="${escHtml(repo.homepage)}" class="card-link card-link-demo" target="_blank" rel="noopener" onclick="event.stopPropagation()" title="Live demo / website">🔗 Demo</a>`
    : "";
  const playLink = hasGooglePlay(repo)
    ? `<a href="https://play.google.com/store/search?q=${encodeURIComponent(repo.name)}" class="card-link card-link-play" target="_blank" rel="noopener" onclick="event.stopPropagation()" title="Google Play">▶ Play</a>`
    : "";

  const card = document.createElement("article");
  card.className = "app-card";
  card.id = `app-${slug}`;
  card.setAttribute("data-category", repo.category);
  card.setAttribute("data-search", `${repo.name} ${repo.description} ${(repo.topics || []).join(" ")}`.toLowerCase());
  card.style.animationDelay = `${Math.min(index * 0.04, 0.6)}s`;

  card.innerHTML = `
    <div class="card-top">
      <div class="app-icon" style="background: linear-gradient(135deg, ${g1}, ${g2})">${letter}</div>
      <div class="card-badges">
        <span class="badge ${langClass(repo.language)}">${escHtml(repo.language || "—")}</span>
        <span class="badge cat-${repo.category}">${cat.icon} ${cat.label}</span>
      </div>
    </div>
    <div class="card-body">
      <h3 class="app-name">${escHtml(repo.name)}</h3>
      <p class="app-desc">${escHtml(repo.description || "No description yet.")}</p>
    </div>
    <div class="card-footer">
      <div class="card-stats">
        ${starsHtml}${forksHtml}${updatedHtml}
      </div>
      <div class="card-links">
        ${demoLink}${playLink}
        <a href="${escHtml(repo.url)}" class="card-link card-link-gh" target="_blank" rel="noopener" onclick="event.stopPropagation()">
          GitHub
        </a>
      </div>
    </div>`;

  card.addEventListener("click", () => window.open(repo.url, "_blank", "noopener"));
  return card;
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ---- State ----
let allRepos = [];
let activeCategory = "all";
let searchQuery = "";
let debounceTimer = null;

function filteredRepos() {
  return allRepos.filter(repo => {
    const catMatch = activeCategory === "all" || repo.category === activeCategory;
    if (!catMatch) return false;
    if (!searchQuery) return true;
    return repo["data-search"] && repo["data-search"].includes(searchQuery);
  });
}

function renderGrid(repos) {
  const grid = document.getElementById("app-grid");
  const empty = document.getElementById("empty-state");
  const resultsText = document.getElementById("results-text");

  grid.innerHTML = "";
  if (repos.length === 0) {
    empty.hidden = false;
    resultsText.textContent = "No apps found";
    return;
  }
  empty.hidden = true;
  resultsText.textContent = `Showing ${repos.length} app${repos.length === 1 ? "" : "s"}`;
  const frag = document.createDocumentFragment();
  repos.forEach((repo, i) => frag.appendChild(createCard(repo, i)));
  grid.appendChild(frag);
}

function setCategory(cat) {
  activeCategory = cat;
  document.querySelectorAll(".pill").forEach(p => {
    p.classList.toggle("active", p.dataset.cat === cat);
  });
  renderGrid(filteredRepos());
  // Update URL hash for bookmarking
  history.replaceState(null, "", cat === "all" ? "#" : `#cat-${cat}`);
}

function onSearch(value) {
  searchQuery = value.trim().toLowerCase();
  const clearBtn = document.getElementById("search-clear");
  if (clearBtn) clearBtn.hidden = !searchQuery;
  renderGrid(filteredRepos());
}

function initControls() {
  // Category pills
  document.querySelectorAll(".pill").forEach(pill => {
    pill.addEventListener("click", () => setCategory(pill.dataset.cat));
  });

  // Main search input
  const searchEl = document.getElementById("search");
  if (searchEl) {
    searchEl.addEventListener("input", e => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => onSearch(e.target.value), 180);
    });
  }

  // Nav search (mirrors main)
  const navSearch = document.getElementById("nav-search");
  if (navSearch) {
    navSearch.addEventListener("input", e => {
      if (searchEl) searchEl.value = e.target.value;
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => onSearch(e.target.value), 180);
      document.getElementById("catalog")?.scrollIntoView({ behavior: "smooth" });
    });
  }

  // Clear button
  const clearBtn = document.getElementById("search-clear");
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      if (searchEl) searchEl.value = "";
      if (navSearch) navSearch.value = "";
      onSearch("");
    });
  }

  // Restore category from URL hash
  const hash = location.hash;
  if (hash.startsWith("#cat-")) {
    const cat = hash.slice(5);
    if (document.querySelector(`[data-cat="${cat}"]`)) setCategory(cat);
  }
}

function populateHero(profile, stats) {
  const avatar = document.getElementById("hero-avatar");
  if (avatar && profile.avatar_url) {
    avatar.src = profile.avatar_url;
    avatar.alt = profile.name;
  }
  const nameEl = document.getElementById("hero-name");
  if (nameEl && profile.name) nameEl.textContent = profile.name;

  const bioEl = document.getElementById("hero-bio");
  if (bioEl && profile.bio) {
    bioEl.textContent = profile.bio.length > 160
      ? profile.bio.slice(0, 157) + "…"
      : profile.bio;
  }

  const statsEl = document.getElementById("hero-stats");
  if (statsEl) {
    const items = [
      { num: stats.total, label: "Apps" },
      { num: stats.total_stars || 0, label: "Stars" },
      { num: stats.by_category?.android || 0, label: "Android" },
      { num: profile.followers || 0, label: "Followers" },
    ];
    statsEl.innerHTML = items.map(s =>
      `<div class="stat-pill">
        <span class="stat-num">${s.num}</span>
        <span class="stat-label">${s.label}</span>
      </div>`
    ).join("");
  }
}

function updatePillCounts(repos, byCategory) {
  const total = repos.length;
  const countAll = document.getElementById("count-all");
  if (countAll) countAll.textContent = total;

  Object.entries(byCategory).forEach(([cat, count]) => {
    const el = document.getElementById(`count-${cat}`);
    if (el) el.textContent = count;
  });
}

function injectJsonLd(catalog) {
  const items = catalog.repos.map((repo, i) => ({
    "@type": "SoftwareApplication",
    "position": i + 1,
    "name": repo.name,
    "description": repo.description || undefined,
    "url": repo.url,
    "applicationCategory": repo.category,
    "operatingSystem": repo.category === "android" ? "Android" : "Web",
  }));

  const ld = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "name": `${catalog.profile.name}'s App Portfolio`,
    "description": "Complete catalog of open-source apps, tools, and platforms",
    "url": catalog.showcase_url,
    "numberOfItems": items.length,
    "itemListElement": items,
  };

  const script = document.getElementById("jsonld");
  if (script) script.textContent = JSON.stringify(ld);
}

// ---- Main ----
async function init() {
  try {
    const res = await fetch("catalog.json?" + Date.now());
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const catalog = await res.json();

    // Attach pre-lowercased search string to each repo object for filtering
    catalog.repos.forEach(r => {
      r["data-search"] = `${r.name} ${r.description} ${(r.topics || []).join(" ")}`.toLowerCase();
    });
    allRepos = catalog.repos;

    populateHero(catalog.profile, catalog.stats);
    updatePillCounts(catalog.repos, catalog.stats.by_category || {});
    initControls();
    renderGrid(filteredRepos());

    const lastUpdated = document.getElementById("last-updated");
    if (lastUpdated && catalog.updated) {
      lastUpdated.textContent = `Updated ${catalog.updated}`;
    }

    injectJsonLd(catalog);
  } catch (err) {
    console.error("Failed to load catalog:", err);
    const grid = document.getElementById("app-grid");
    if (grid) {
      grid.innerHTML = `
        <div style="grid-column:1/-1;text-align:center;padding:60px 24px;color:var(--text-2)">
          <div style="font-size:2.5rem;margin-bottom:12px">⚠️</div>
          <p>Couldn't load the catalog. <a href="https://github.com/chartmann1590" style="color:var(--blue);text-decoration:underline">Browse on GitHub</a></p>
        </div>`;
    }
    document.getElementById("results-text").textContent = "Error loading catalog";
  }
}

document.addEventListener("DOMContentLoaded", init);
