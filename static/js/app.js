/**
 * ViralNews Studio - Core Frontend Application Controller
 * Handles News Aggregation (Urdu & English), Bulk Selection, Live Studio (8 Themes),
 * Real Social Publishing (Facebook Meta Graph API, Telegram, TikTok), and Auto-Pilot.
 */

let appState = {
  currentCategory: 'trending',
  currentLanguage: 'english', // default to English for fast initial load (switch to Urdu via button)
  currentCity: 'Lahore',
  articles: [],
  selectedArticleIds: new Set(),
  settings: {},
  generatedZipFilenames: []
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initCanvasStudio();
  loadAppSettings();
  loadNewsFeed(appState.currentCategory, null, false);
  loadPostHistory();
  loadPostQueue();
  loadMetaRateLimitStatus();
  loadSchedulerLogs();
});

// Toast notification helper
function showToast(title, message, isSuccess = true) {
  const toastEl = document.getElementById('liveToast');
  if (!toastEl) return;
  document.getElementById('toastTitle').innerText = title;
  document.getElementById('toastMessage').innerText = message;
  const icon = document.getElementById('toastIcon');
  if (icon) {
    icon.className = isSuccess ? 'fa-solid fa-circle-check text-success me-2' : 'fa-solid fa-triangle-exclamation text-warning me-2';
  }
  const toast = new bootstrap.Toast(toastEl, { delay: 4500 });
  toast.show();
}

function switchTab(tabId) {
  const triggerEl = document.querySelector(`button[data-bs-target="#${tabId}"]`);
  if (triggerEl) {
    const tab = new bootstrap.Tab(triggerEl);
    tab.show();
  }
  if (tabId === 'tab-history') {
    loadPostHistory();
    loadPostQueue();
    loadMetaRateLimitStatus();
  } else if (tabId === 'tab-settings') {
    loadMetaRateLimitStatus();
  } else if (tabId === 'tab-autopilot') {
    loadSchedulerLogs();
  }
}

document.addEventListener('shown.bs.tab', (e) => {
  const targetId = e.target.getAttribute('data-bs-target')?.replace('#', '');
  if (targetId === 'tab-history') {
    loadPostHistory();
    loadPostQueue();
    loadMetaRateLimitStatus();
  } else if (targetId === 'tab-settings') {
    loadMetaRateLimitStatus();
  }
});

function decodeHtmlEntities(str) {
  if (!str) return '';
  const txt = document.createElement("textarea");
  txt.innerHTML = str;
  return txt.value.replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim();
}

// ==========================================
// 1. LANGUAGE SWITCHER (URDU / ENGLISH)
// ==========================================
function setLanguage(lang) {
  appState.currentLanguage = lang;
  
  const urduBtn = document.getElementById('langUrduBtn');
  const enBtn = document.getElementById('langEnBtn');
  const langBadge = document.getElementById('currentLangBadge');

  if (lang === 'urdu') {
    urduBtn.className = 'btn btn-danger btn-lang active';
    enBtn.className = 'btn btn-outline-secondary btn-lang text-white';
    if (langBadge) {
      langBadge.className = 'badge bg-danger';
      langBadge.innerText = 'URDU / RTL (اردو)';
    }
  } else {
    enBtn.className = 'btn btn-primary btn-lang active';
    urduBtn.className = 'btn btn-outline-secondary btn-lang text-white';
    if (langBadge) {
      langBadge.className = 'badge bg-primary';
      langBadge.innerText = 'ENGLISH';
    }
  }

  // Reload feed for new language
  loadNewsFeed(appState.currentCategory, null, true);
}

// ==========================================
// 2. SETTINGS & FACEBOOK CONNECTION
// ==========================================
async function loadAppSettings() {
  try {
    const res = await fetch('/api/settings');
    const data = await res.json();
    if (data.success) {
      appState.settings = data.settings;
      applySettingsToUI(data.settings);
    }
  } catch (err) {
    console.error('Error loading settings:', err);
  }
}

function applySettingsToUI(settings) {
  if (settings.local_city) {
    appState.currentCity = settings.local_city;
    const cityEl = document.getElementById('currentLocalCity');
    if (cityEl) cityEl.innerText = settings.local_city;
    const settingCityEl = document.getElementById('settingLocalCity');
    if (settingCityEl) settingCityEl.value = settings.local_city;
  }
  if (settings.page_name) {
    document.getElementById('settingPageName').value = settings.page_name;
    document.getElementById('studioPageNameInput').value = settings.page_name;
  }
  if (settings.page_handle) {
    document.getElementById('settingPageHandle').value = settings.page_handle;
    document.getElementById('studioHandleInput').value = settings.page_handle;
  }
  if (settings.fb_page_id) document.getElementById('settingFbPageId').value = settings.fb_page_id;
  if (settings.fb_access_token) document.getElementById('settingFbToken').value = settings.fb_access_token;
  if (settings.webhook_url) document.getElementById('settingWebhookUrl').value = settings.webhook_url;
  if (settings.telegram_bot_token) document.getElementById('settingTgToken').value = settings.telegram_bot_token;
  if (settings.telegram_channel_id) document.getElementById('settingTgChannel').value = settings.telegram_channel_id;
  
  // Real posting mode switch (true if simulation_mode is false)
  const isRealPosting = (settings.simulation_mode === 'false');
  const realSwitch = document.getElementById('settingRealModeSwitch');
  if (realSwitch) realSwitch.checked = isRealPosting;
  updatePostingBadge(isRealPosting);

  // Auto-Pilot switch & status
  const autopilotEnabled = (settings.autopilot_enabled === 'true');
  const apSwitch = document.getElementById('autoPilotSwitch');
  if (apSwitch) apSwitch.checked = autopilotEnabled;

  const apPill = document.getElementById('autopilotStatusPill');
  const apText = document.getElementById('autopilotStatusText');
  const apBadge = document.getElementById('autopilotStatusBadge');
  
  if (autopilotEnabled) {
    if (apPill) apPill.className = 'badge rounded-pill bg-success px-3 py-2 d-flex align-items-center gap-1 cursor-pointer';
    if (apText) apText.innerText = `Auto-Pilot: Active (${settings.autopilot_interval_hours || 4}h)`;
    if (apBadge) {
      apBadge.className = 'badge bg-success';
      apBadge.innerText = 'ACTIVE';
    }
  } else {
    if (apPill) apPill.className = 'badge rounded-pill bg-secondary px-3 py-2 d-flex align-items-center gap-1 cursor-pointer';
    if (apText) apText.innerText = 'Auto-Pilot: Paused';
    if (apBadge) {
      apBadge.className = 'badge bg-secondary';
      apBadge.innerText = 'DISABLED';
    }
  }

  if (settings.autopilot_interval_hours && document.getElementById('autoPilotInterval')) {
    document.getElementById('autoPilotInterval').value = settings.autopilot_interval_hours;
  }
  if (settings.autopilot_category && document.getElementById('autoPilotCategory')) {
    document.getElementById('autoPilotCategory').value = settings.autopilot_category;
  }
  if (settings.autopilot_max_posts && document.getElementById('autoPilotMaxPosts')) {
    document.getElementById('autoPilotMaxPosts').value = settings.autopilot_max_posts;
  }
  if (settings.post_interval_minutes && document.getElementById('settingPublishInterval')) {
    document.getElementById('settingPublishInterval').value = settings.post_interval_minutes;
  }
}

function updatePostingBadge(isReal) {
  const badge = document.getElementById('postingModeBadge');
  if (!badge) return;
  if (isReal) {
    badge.className = 'badge bg-success';
    badge.innerText = '🔴 REAL LIVE POSTING ACTIVATED';
  } else {
    badge.className = 'badge bg-warning text-dark';
    badge.innerText = '🟡 SIMULATION / SAFE MODE';
  }
}

function togglePostingMode(isReal) {
  updatePostingBadge(isReal);
  // Auto-save setting
  fetch('/api/settings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ settings: { simulation_mode: isReal ? 'false' : 'true' } })
  });
  showToast(isReal ? 'Real Mode Active' : 'Simulation Mode Active', 
    isReal ? 'All posts will now publish to your live Facebook Page / Telegram!' : 'Posts will run safely in simulation mode.');
}

function toggleTokenVisibility() {
  const tokenInput = document.getElementById('settingFbToken');
  const eyeIcon = document.getElementById('tokenEyeIcon');
  if (tokenInput.type === 'password') {
    tokenInput.type = 'text';
    eyeIcon.className = 'fa-solid fa-eye-slash';
  } else {
    tokenInput.type = 'password';
    eyeIcon.className = 'fa-solid fa-eye';
  }
}

async function testFacebookToken() {
  const pageId = document.getElementById('settingFbPageId').value.trim();
  const token = document.getElementById('settingFbToken').value.trim();
  const resDiv = document.getElementById('fbTestResult');

  if (!pageId || !token) {
    showToast('Missing Credentials', 'Please enter both Page ID and Page Access Token first.', false);
    return;
  }

  resDiv.className = 'small mt-2 alert alert-info py-2';
  resDiv.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Connecting to Meta Graph API...';
  resDiv.classList.remove('d-none');

  try {
    const res = await fetch('/api/social/test-facebook', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ page_id: pageId, access_token: token })
    });
    const data = await res.json();

    if (data.success) {
      resDiv.className = 'small mt-2 alert alert-success py-2 fw-bold';
      resDiv.innerHTML = `<i class="fa-solid fa-circle-check text-success me-1"></i> Connected to: "${data.page_name}" (ID: ${data.page_id})`;
      showToast('Connection Successful!', `Verified Facebook Page: ${data.page_name}`);
      loadMetaRateLimitStatus();
    } else {
      resDiv.className = 'small mt-2 alert alert-danger py-2';
      resDiv.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-danger me-1"></i> ${data.error}`;
      showToast('Connection Failed', data.error, false);
      loadMetaRateLimitStatus();
    }
  } catch (err) {
    resDiv.className = 'small mt-2 alert alert-danger py-2';
    resDiv.innerText = 'Network error while testing Facebook connection.';
  }
}

async function saveAllAppSettings() {
  const payload = {
    page_name: document.getElementById('settingPageName').value,
    page_handle: document.getElementById('settingPageHandle').value,
    local_city: document.getElementById('settingLocalCity').value,
    default_theme: document.getElementById('settingDefaultTheme').value,
    default_aspect_ratio: document.getElementById('settingDefaultRatio').value,
    fb_page_id: document.getElementById('settingFbPageId').value.trim(),
    fb_access_token: document.getElementById('settingFbToken').value.trim(),
    webhook_url: document.getElementById('settingWebhookUrl').value.trim(),
    telegram_bot_token: document.getElementById('settingTgToken').value.trim(),
    telegram_channel_id: document.getElementById('settingTgChannel').value.trim(),
    post_interval_minutes: document.getElementById('settingPublishInterval') ? document.getElementById('settingPublishInterval').value : '45',
    simulation_mode: document.getElementById('settingRealModeSwitch').checked ? 'false' : 'true'
  };

  try {
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ settings: payload })
    });
    const data = await res.json();
    if (data.success) {
      showToast('Settings Saved', 'Branding, API tokens, and real-posting settings saved.');
      loadAppSettings();
    }
  } catch (err) {
    showToast('Error', 'Failed to save settings.', false);
  }
}

// ==========================================
// 3. NEWS FEED & CATEGORIES
// ==========================================
function setCategory(cat) {
  appState.currentCategory = cat;
  document.querySelectorAll('.btn-category').forEach(b => b.classList.remove('active'));
  const btn = document.querySelector(`[data-cat="${cat}"]`);
  if (btn) btn.classList.add('active');
  loadNewsFeed(cat, null, false);
}

async function refreshFeed(forceLive = false) {
  const icon = document.getElementById('refreshIcon');
  if (icon) icon.classList.add('fa-spin');
  await loadNewsFeed(appState.currentCategory, null, forceLive);
  if (icon) icon.classList.remove('fa-spin');
}

function executeSearch() {
  const query = document.getElementById('newsSearchInput').value.trim();
  if (query) {
    loadNewsFeed('search', query, true);
  }
}

async function loadNewsFeed(category = 'trending', query = null, refresh = false) {
  const spinner = document.getElementById('newsLoadingSpinner');
  const grid = document.getElementById('newsGrid');
  
  if (spinner) spinner.classList.remove('d-none');
  if (grid && refresh) grid.innerHTML = '';

  try {
    let url = `/api/news?category=${category}&city=${encodeURIComponent(appState.currentCity)}&language=${appState.currentLanguage}&refresh=${refresh}`;
    if (query) url += `&query=${encodeURIComponent(query)}`;

    const res = await fetch(url);
    const data = await res.json();

    if (data.success) {
      appState.articles = data.articles;
      renderNewsGrid(data.articles);
    }
  } catch (err) {
    console.error('Error fetching news:', err);
    showToast('Feed Error', 'Could not load news feed.', false);
  } finally {
    if (spinner) spinner.classList.add('d-none');
  }
}

function renderNewsGrid(articles) {
  const grid = document.getElementById('newsGrid');
  if (!grid) return;

  if (articles.length === 0) {
    grid.innerHTML = `
      <div class="col-12 text-center py-5 text-white">
        <i class="fa-regular fa-newspaper fa-3x mb-3 text-danger"></i>
        <h5 class="fw-bold">No news articles found</h5>
        <p class="small text-white">Click "Refresh Live" or switch between Urdu and English.</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = articles.map(art => {
    const isSelected = appState.selectedArticleIds.has(art.id);
    const categoryBadge = getCategoryBadgeLabel(art.category, art.language);
    const fallbackImg = 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=1080&auto=format&fit=crop&q=80';
    const displayImg = art.image_url || fallbackImg;
    const cleanTitle = decodeHtmlEntities(art.title);
    const cleanSummary = decodeHtmlEntities(art.summary || art.title);
    const isUrdu = (art.language === 'urdu' || /[\u0600-\u06FF]/.test(cleanTitle));

    return `
      <div class="col-12 col-md-6 col-lg-4 col-xl-3">
        <div class="news-feed-card ${isSelected ? 'selected' : ''}" id="card-${art.id}">
          
          <!-- Image & Badges -->
          <div class="card-thumb-wrapper">
            <div class="thumb-checkbox-overlay">
              <input class="form-check-input art-checkbox" type="checkbox" id="chk-${art.id}" 
                     ${isSelected ? 'checked' : ''} onchange="toggleArticleSelection('${art.id}', this.checked)">
            </div>
            <img src="${displayImg}" class="card-thumb-img" alt="News Image" onerror="this.src='${fallbackImg}'">
            <span class="thumb-category-badge">${categoryBadge}</span>
          </div>

          <!-- Content Details -->
          <div class="card-content-wrap ${isUrdu ? 'urdu-text' : ''}">
            
            <div class="card-meta-bar mb-2 d-flex justify-content-between align-items-center">
              <span class="badge bg-dark border border-secondary text-light fw-bold px-2 py-1">
                <i class="fa-solid fa-newspaper me-1 text-danger"></i>${escapeHtml(art.source)}
              </span>
              <span class="small text-light opacity-75">
                <i class="fa-regular fa-clock me-1"></i>${formatTimeAgo(art.published_at)}
              </span>
            </div>

            <h6 class="news-title fw-bold text-white mb-2" title="${escapeHtml(cleanTitle)}">${escapeHtml(cleanTitle)}</h6>
            <p class="news-summary text-light opacity-75 small mb-3">${escapeHtml(cleanSummary)}</p>

            <!-- Card Action Buttons -->
            <div class="card-actions-row d-flex gap-2 mt-auto pt-2 border-top border-secondary">
              <button class="btn btn-sm btn-danger flex-grow-1 fw-bold text-white shadow-sm" onclick="openInStudio('${art.id}')" title="Customize in Studio">
                <i class="fa-solid fa-palette me-1"></i> Open Studio
              </button>
              <button class="btn btn-sm btn-outline-info text-white fw-bold px-2" onclick="quickGenerateVideo('${art.id}')" title="Generate Short 9:16 Video">
                <i class="fa-solid fa-video me-1"></i> Video
              </button>
              <a href="${art.link}" target="_blank" class="btn btn-sm btn-outline-light text-white px-2" title="Original Story">
                <i class="fa-solid fa-arrow-up-right-from-square"></i>
              </a>
            </div>

          </div>

        </div>
      </div>
    `;
  }).join('');

  updateBulkToolbar();
}

function getCategoryBadgeLabel(cat, lang) {
  const isUrdu = (lang === 'urdu');
  switch ((cat || '').toLowerCase()) {
    case 'pakistan': return isUrdu ? '🇵🇰 پاکستان' : '🇵🇰 Pakistan';
    case 'local': return isUrdu ? `📍 ${appState.currentCity}` : `📍 ${appState.currentCity}`;
    case 'world': return isUrdu ? '🌍 دنیا' : '🌍 World';
    default: return isUrdu ? '🔥 بریکنگ' : '🔥 Trending';
  }
}

function formatTimeAgo(dateStr) {
  if (!dateStr) return 'Recent';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return 'Today';
    const mins = Math.floor((new Date() - d) / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  } catch (e) {
    return 'Recent';
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// ==========================================
// 4. BULK SELECTION ACTIONS
// ==========================================
function toggleArticleSelection(artId, isChecked) {
  if (isChecked) {
    appState.selectedArticleIds.add(artId);
  } else {
    appState.selectedArticleIds.delete(artId);
  }
  
  const card = document.getElementById(`card-${artId}`);
  if (card) {
    if (isChecked) card.classList.add('selected');
    else card.classList.remove('selected');
  }

  updateBulkToolbar();
}

function toggleSelectAll(isChecked) {
  appState.articles.forEach(art => {
    if (isChecked) {
      appState.selectedArticleIds.add(art.id);
    } else {
      appState.selectedArticleIds.delete(art.id);
    }
    const chk = document.getElementById(`chk-${art.id}`);
    if (chk) chk.checked = isChecked;
    const card = document.getElementById(`card-${art.id}`);
    if (card) {
      if (isChecked) card.classList.add('selected');
      else card.classList.remove('selected');
    }
  });
  updateBulkToolbar();
}

function selectTopN(count) {
  clearSelection();
  appState.articles.slice(0, count).forEach(art => {
    appState.selectedArticleIds.add(art.id);
    const chk = document.getElementById(`chk-${art.id}`);
    if (chk) chk.checked = true;
    const card = document.getElementById(`card-${art.id}`);
    if (card) card.classList.add('selected');
  });
  updateBulkToolbar();
}

function clearSelection() {
  appState.selectedArticleIds.clear();
  document.querySelectorAll('.art-checkbox').forEach(chk => chk.checked = false);
  document.querySelectorAll('.news-feed-card').forEach(c => c.classList.remove('selected'));
  const selectAll = document.getElementById('selectAllCheckbox');
  if (selectAll) selectAll.checked = false;
  updateBulkToolbar();
}

function updateBulkToolbar() {
  const count = appState.selectedArticleIds.size;
  const badge = document.getElementById('selectedCountBadge');
  if (badge) badge.innerText = `${count} Selected`;

  document.querySelectorAll('.selected-num').forEach(el => el.innerText = count);

  const disabled = (count === 0);
  document.getElementById('bulkGenBtn').disabled = disabled;
  document.getElementById('bulkPostBtn').disabled = disabled;
  document.getElementById('bulkZipBtn').disabled = (appState.generatedZipFilenames.length === 0 && count === 0);
}

async function bulkGenerateCards() {
  const ids = Array.from(appState.selectedArticleIds);
  if (ids.length === 0) return;

  const btn = document.getElementById('bulkGenBtn');
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Rendering (${ids.length})...`;

  try {
    const res = await fetch('/api/cards/bulk-generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        article_ids: ids,
        theme: appState.settings.default_theme || 'breaking_red',
        aspect_ratio: appState.settings.default_aspect_ratio || '1:1',
        page_name: appState.settings.page_name || 'PAK NEWS 24/7',
        page_handle: appState.settings.page_handle || '@PakNewsOfficial'
      })
    });
    const data = await res.json();
    if (data.success) {
      appState.generatedZipFilenames = data.cards.map(c => c.card.filename);
      showToast('Bulk Generated!', `Successfully rendered ${data.total_generated} broadcast graphics!`);
      document.getElementById('bulkZipBtn').disabled = false;
    }
  } catch (err) {
    showToast('Error', 'Bulk generation failed.', false);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles me-1"></i> Bulk Generate Graphics (${ids.length})`;
  }
}

async function bulkDownloadZip() {
  if (appState.generatedZipFilenames.length === 0) {
    await bulkGenerateCards();
  }

  if (appState.generatedZipFilenames.length === 0) return;

  try {
    const res = await fetch('/api/cards/download-zip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filenames: appState.generatedZipFilenames })
    });
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ViralNews_Batch_${appState.generatedZipFilenames.length}_Graphics.zip`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    showToast('ZIP Downloaded', 'Bulk news graphics package downloaded!');
  } catch (err) {
    showToast('Download Error', 'Could not create ZIP.', false);
  }
}

function bulkPostModal() {
  const count = appState.selectedArticleIds.size;
  if (count === 0) return;
  document.getElementById('modalBulkCount').innerText = count;
  const modal = new bootstrap.Modal(document.getElementById('bulkPostModalElement'));
  modal.show();
}

async function executeBulkPost() {
  const ids = Array.from(appState.selectedArticleIds);
  const target = document.getElementById('modalBulkTarget').value;
  const theme = document.getElementById('modalBulkTheme').value;
  const spinner = document.getElementById('bulkPostSpinner');
  if (spinner) spinner.classList.remove('d-none');

  try {
    const genRes = await fetch('/api/cards/bulk-generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        article_ids: ids,
        theme: theme,
        aspect_ratio: '1:1',
        page_name: appState.settings.page_name,
        page_handle: appState.settings.page_handle
      })
    });
    const genData = await genRes.json();

    if (genData.success && genData.cards.length > 0) {
      const itemsToPost = genData.cards.map(c => {
        const art = appState.articles.find(a => a.id === c.article_id);
        return {
          image_path: c.card.file_path,
          caption: generateViralCaptionClient(art || { title: c.title }),
          article: art
        };
      });

      const postRes = await fetch('/api/social/bulk-post', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items: itemsToPost, target: target })
      });
      const postData = await postRes.json();

      if (postData.success) {
        bootstrap.Modal.getInstance(document.getElementById('bulkPostModalElement')).hide();
        showToast('Bulk Post Complete', `Published ${postData.processed} posts!`);
        clearSelection();
        loadPostHistory();
      }
    }
  } catch (err) {
    showToast('Post Error', 'Bulk posting encountered an issue.', false);
  } finally {
    if (spinner) spinner.classList.add('d-none');
  }
}

// ==========================================
// 5. STUDIO INTEGRATION & LIVE POSTING
// ==========================================
function openInStudio(articleId) {
  const art = appState.articles.find(a => a.id === articleId);
  if (!art) return;

  // Make article available globally for video generation
  window.studioArticle = art;

  switchTab('tab-studio');

  const cleanTitle = decodeHtmlEntities(art.title);
  const cleanSummary = decodeHtmlEntities(art.summary || art.title);
  const cleanSource = decodeHtmlEntities(art.source || 'News Desk').toUpperCase();
  const isUrdu = (art.language === 'urdu' || /[\u0600-\u06FF]/.test(cleanTitle));

  document.getElementById('studioTitleInput').value = cleanTitle;
  document.getElementById('studioSummaryInput').value = cleanSummary;
  document.getElementById('studioSourceInput').value = cleanSource;
  
  // Badge
  let badge = isUrdu ? '🔴 بریکنگ نیوز' : '🔴 BREAKING NEWS';
  if (art.category === 'pakistan') badge = isUrdu ? '🇵🇰 پاکستان تازہ ترین' : '🇵🇰 PAKISTAN UPDATE';
  else if (art.category === 'local') badge = isUrdu ? `📍 ${appState.currentCity} خبر` : `📍 ${appState.currentCity.toUpperCase()} REPORT`;
  else if (art.category === 'world') badge = isUrdu ? '🌍 بین الاقوامی خبر' : '🌍 WORLD HEADLINES';
  document.getElementById('studioTagInput').value = badge;

  const imgUrl = art.image_url || THEMATIC_BACKDROPS.breaking;
  document.getElementById('studioImageUrlInput').value = imgUrl;

  document.getElementById('studioCaptionInput').value = generateViralCaptionClient(art);

  currentStudioState.title = cleanTitle;
  currentStudioState.summary = cleanSummary;
  currentStudioState.source = cleanSource;
  currentStudioState.tag = badge;
  currentStudioState.imageUrl = imgUrl;

  const targetTheme = currentStudioState.theme || (appState.settings && appState.settings.default_theme) || 'turkiye_urdu_split';
  setStudioTheme(targetTheme);

  loadStudioImage(imgUrl);
}

function generateViralCaptionClient(article) {
  const cat = (article.category || 'breaking').toLowerCase();
  const title = decodeHtmlEntities(article.title || '');
  const summary = decodeHtmlEntities(article.summary || article.title || '');
  const source = decodeHtmlEntities(article.source || 'News Desk');
  const isUrdu = /[\u0600-\u06FF]/.test(title);
  const pageHandle = appState.settings.page_handle || '@PakNewsOfficial';

  if (isUrdu) {
    let prefix = '🚨 【 بریکنگ نیوز 】';
    let urduTags = '#تازہ_ترین #بریکنگ_نیوز #پاکستان #اہم_خبر';
    let enTags = '#BreakingNews #UrduNews #Pakistan';
    if (cat === 'pakistan') {
      prefix = '🇵🇰 【 پاکستان کی بڑی خبر 】';
      urduTags = '#پاکستان #تازہ_ترین #اہم_خبر #خبریں';
      enTags = '#PakistanNews #Pakistan #UrduNews #GeoNews #DawnNews';
    } else if (cat === 'local') {
      prefix = `📍 【 ${appState.currentCity} کی خبر 】`;
      urduTags = `#${appState.currentCity} #پاکستان #لوکل_نیوز #تازہ_ترین`;
      enTags = `#${appState.currentCity}News #LocalNews #Pakistan #UrduNews`;
    } else if (cat === 'world') {
      prefix = '🌍 【 عالمی خبریں 】';
      urduTags = '#دنیا_کی_خبریں #عالمی_خبریں #بین_الاقوامی #تازہ_ترین';
      enTags = '#WorldNews #InternationalNews #UrduNews';
    }
    return `${prefix}
📢 ${title}

📌 اہم تفصیلات:
• ${summary}

📰 ذرائع: \u200E${source}\u200F
👉 مزید خبروں اور ویڈیوز کے لیے فالو کریں: \u200E${pageHandle}\u200F
💬 اس خبر پر اپنی رائے نیچے کمنٹس میں ضرور لکھیں 👇

${urduTags}
${enTags}`;
  } else {
    let prefix = '🚨 【 BREAKING NEWS 】';
    let tags = '#BreakingNews #NewsAlert #LatestNews #Viral';
    if (cat === 'pakistan') {
      prefix = '🇵🇰 【 PAKISTAN UPDATE 】';
      tags = '#PakistanNews #Pakistan #BreakingNews #GeoNews #DawnNews #ViralPakistan';
    } else if (cat === 'local') {
      prefix = `📍 【 ${appState.currentCity.toUpperCase()} NEWS 】`;
      tags = `#${appState.currentCity}News #LocalNews #Pakistan #CityUpdates`;
    } else if (cat === 'world') {
      prefix = '🌍 【 WORLD HEADLINES 】';
      tags = '#WorldNews #GlobalHeadlines #InternationalNews #DailyNews';
    }

    return `${prefix}
📢 ${title}

📌 Key Highlights:
• ${summary}

📰 Source: ${source}
👉 Follow ${pageHandle} for 24/7 verified updates!
💬 What are your thoughts? Drop your comments below 👇

${tags}`;
  }
}

function copyStudioCaption() {
  const caption = document.getElementById('studioCaptionInput').value;
  navigator.clipboard.writeText(caption).then(() => {
    showToast('Caption Copied!', 'Social caption and hashtags copied to clipboard.');
  });
}

function applyCaptionTemplate(type = 'viral') {
  const title = decodeHtmlEntities(document.getElementById('studioTitleInput')?.value || '');
  const summary = decodeHtmlEntities(document.getElementById('studioSummaryInput')?.value || '');
  const source = decodeHtmlEntities(document.getElementById('studioSourceInput')?.value || 'News Desk');
  const pageHandle = (appState.settings && appState.settings.page_handle) || '@PakNewsOfficial';
  const isUrdu = /[\u0600-\u06FF]/.test(title);

  let output = '';

  if (type === 'breaking') {
    if (isUrdu) {
      output = `⚡ 【 بریکنگ نیوز الرٹ 】
📢 ${title}

📰 ذرائع: \u200E${source}\u200F
👉 فالو کریں: \u200E${pageHandle}\u200F

#بریکنگ_نیوز #تازہ_ترین #پاکستان
#BreakingNews #UrduNews`;
    } else {
      output = `⚡ 【 BREAKING NEWS ALERT 】
📢 ${title}

📰 Source: ${source}
👉 Follow: ${pageHandle}

#BreakingNews #LatestNews #NewsAlert`;
    }
  } else if (type === 'bullets') {
    if (isUrdu) {
      const bulletItems = summary.split(/[۔\n\.]+/).filter(s => s.trim().length > 5);
      const formattedBullets = bulletItems.map(b => `• ${b.trim()}`).join('\n') || `• ${summary}`;
      output = `📌 【 اہم خبر کی تفصیلات 】
📢 ${title}

اہم نکات:
${formattedBullets}

📰 ذرائع: \u200E${source}\u200F
👉 مزید اپڈیٹس کے لیے فالو کریں: \u200E${pageHandle}\u200F

#پاکستان #اہم_خبر #خبریں
#PakistanNews #UrduUpdates`;
    } else {
      output = `📌 【 KEY HIGHLIGHTS 】
📢 ${title}

Key Points:
• ${summary}

📰 Source: ${source}
👉 Follow ${pageHandle} for more!

#NewsUpdates #Highlights #DailyNews`;
    }
  } else if (type === 'english') {
    output = `🚨 【 VIRAL NEWS HEADLINE 】
📢 ${title}

📌 Summary:
• ${summary || title}

📰 Source: ${source}
👉 Follow ${pageHandle} for 24/7 verified coverage!
💬 What is your opinion on this? Comment below 👇

#BreakingNews #ViralNews #Pakistan #WorldNews #Headlines`;
  } else {
    // Default viral
    output = generateViralCaptionClient({
      title, summary, source, category: appState.currentCategory
    });
  }

  const captionInput = document.getElementById('studioCaptionInput');
  if (captionInput) {
    captionInput.value = output;
    captionInput.setAttribute('dir', isUrdu && type !== 'english' ? 'rtl' : 'ltr');
  }
}

function regenerateStudioCaption() {
  applyCaptionTemplate('viral');
}

function openTikTokPublishModal() {
  setStudioRatio('9:16');
  const modal = new bootstrap.Modal(document.getElementById('tiktokModal'));
  modal.show();
}

async function publishStudioPost(platform = 'facebook') {
  if (!canvas) return;

  const caption = document.getElementById('studioCaptionInput').value;
  showToast('Publishing...', `Preparing broadcast card and sending to ${platform}...`);

  const title = document.getElementById('studioTitleInput').value;

  try {
    // 1. Capture exact live canvas so what user sees is 100% what is published
    const canvasDataUrl = canvas.toDataURL('image/png', 0.96);
    const upRes = await fetch('/api/cards/upload-canvas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_data: canvasDataUrl,
        title: title,
        filename_prefix: `studio_${currentStudioState.theme}`
      })
    });
    const upData = await upRes.json();

    if (upData.success) {
      const imgPath = upData.file_path;
      let postEndpoint = '/api/social/post-facebook';
      if (platform === 'webhook') postEndpoint = '/api/social/post-webhook';
      if (platform === 'telegram') postEndpoint = '/api/social/post-telegram';

      const postRes = await fetch(postEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_path: imgPath, caption: caption })
      });
      const postResult = await postRes.json();

      if (postResult.success) {
        showToast('Published!', postResult.message || `Post published successfully to ${platform}!`);
        loadPostHistory();
      } else {
        showToast('Post Notice', postResult.error || 'Failed to publish post.', false);
        loadMetaRateLimitStatus();
      }
    } else {
      showToast('Error', 'Failed to prepare canvas graphic.', false);
    }
  } catch (err) {
    showToast('Publish Error', 'Error publishing post: ' + err.message, false);
  }
}

// ==========================================
// 6. AUTO-PILOT SCHEDULER CONTROLS
// ==========================================
async function toggleAutoPilot(enabled) {
  try {
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        settings: { autopilot_enabled: enabled ? 'true' : 'false' }
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast(enabled ? 'Auto-Pilot Activated' : 'Auto-Pilot Paused', 
        enabled ? 'Background worker is now automatically monitoring and posting news.' : 'Auto-pilot paused.');
      loadAppSettings();
      loadSchedulerLogs();
    }
  } catch (err) {
    showToast('Error', 'Failed to toggle Auto-Pilot.', false);
  }
}

async function triggerAutoPilotNow() {
  showToast('Auto-Pilot Started', 'Finding breaking news and generating posts...');
  try {
    const res = await fetch('/api/settings/autopilot/trigger', { method: 'POST' });
    const data = await res.json();
    if (data.status === 'success') {
      showToast('Cycle Complete', `Auto-Pilot completed! Posted ${data.posted_count} new articles.`);
      loadSchedulerLogs();
      loadPostHistory();
    } else {
      showToast('Status', data.message || 'Auto-pilot completed run.');
    }
  } catch (err) {
    showToast('Auto-Pilot Error', 'Manual run failed.', false);
  }
}

async function saveAutoPilotSettings() {
  const payload = {
    autopilot_interval_hours: document.getElementById('autoPilotInterval').value,
    autopilot_category: document.getElementById('autoPilotCategory').value,
    autopilot_max_posts: document.getElementById('autoPilotMaxPosts').value
  };

  try {
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ settings: payload })
    });
    const data = await res.json();
    if (data.success) {
      showToast('Settings Saved', 'Scheduler interval and parameters updated.');
      loadAppSettings();
    }
  } catch (err) {
    showToast('Error', 'Failed to save scheduler settings.', false);
  }
}

async function loadSchedulerLogs() {
  const tbody = document.getElementById('schedulerLogsBody');
  if (!tbody) return;

  try {
    const res = await fetch('/api/settings/autopilot/logs');
    const data = await res.json();
    if (data.success && data.logs.length > 0) {
      tbody.innerHTML = data.logs.map(log => {
        const statusBadge = log.status === 'success' 
          ? '<span class="badge bg-success">Success</span>' 
          : (log.status === 'error' ? '<span class="badge bg-danger">Error</span>' : '<span class="badge bg-info">Info</span>');
        
        const time = log.created_at ? log.created_at.replace('T', ' ').slice(11, 19) : '';
        return `
          <tr>
            <td class="text-white">${time}</td>
            <td class="fw-bold text-white">${escapeHtml(log.action)}</td>
            <td class="text-white">${escapeHtml(log.message)}</td>
            <td>${statusBadge}</td>
          </tr>
        `;
      }).join('');
    } else {
      tbody.innerHTML = `<tr><td colspan="4" class="text-center text-white py-3">No logs recorded yet.</td></tr>`;
    }
  } catch (err) {
    console.error('Error loading scheduler logs:', err);
  }
}

// ==========================================
// 7. HISTORY & QUEUE
// ==========================================
async function loadPostHistory() {
  const tbody = document.getElementById('historyTableBody');
  const countBadge = document.getElementById('historySuccessCount');

  try {
    const res = await fetch('/api/social/history');
    const data = await res.json();
    if (data.success && data.history.length > 0) {
      if (countBadge) countBadge.innerText = data.history.length;
      if (tbody) {
        tbody.innerHTML = data.history.map(item => {
          const imgName = item.card_image_path ? item.card_image_path.split(/[\\/]/).pop() : '';
          const imgWebUrl = `/static/generated/${imgName}`;
          const isSimulated = (item.status === 'simulated');
          const isVideo = imgName.toLowerCase().endsWith('.mp4');
          const badgeClass = isSimulated ? 'bg-warning text-dark' : (item.status === 'published' ? 'bg-success' : 'bg-danger');

          return `
            <tr>
              <td>
                <div class="position-relative">
                  <img src="${isVideo ? 'https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=120' : imgWebUrl}" class="rounded border border-secondary" style="width: 70px; height: 70px; object-fit: cover;" onerror="this.src='https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=120'">
                  ${isVideo ? '<span class="position-absolute bottom-0 end-0 badge bg-danger p-1"><i class="fa-solid fa-video"></i></span>' : ''}
                </div>
              </td>
              <td>
                <div class="fw-bold text-white">${escapeHtml(item.title)}</div>
                <div class="small text-white text-truncate" style="max-width: 400px;">${escapeHtml(item.caption.split('\n')[1] || item.caption)}</div>
                ${item.error_message ? `<div class="small text-danger mt-1"><i class="fa-solid fa-triangle-exclamation me-1"></i>${escapeHtml(item.error_message)}</div>` : ''}
              </td>
              <td>
                <span class="badge bg-dark border border-secondary text-white"><i class="fa-brands fa-facebook text-primary me-1"></i>${item.platform}</span>
              </td>
              <td>
                <span class="badge ${badgeClass} fw-bold">${item.status.toUpperCase()}</span>
              </td>
              <td class="small text-white">${item.published_at ? item.published_at.replace('T', ' ').slice(0, 16) : ''}</td>
              <td>
                <a href="${imgWebUrl}" download class="btn btn-sm btn-outline-light text-white" title="Download Media"><i class="fa-solid fa-download"></i></a>
              </td>
            </tr>
          `;
        }).join('');
      }
    } else {
      if (countBadge) countBadge.innerText = '0';
      if (tbody) tbody.innerHTML = `<tr><td colspan="6" class="text-center text-white py-4">No published history yet. Generate and post articles to see them here.</td></tr>`;
    }
  } catch (err) {
    console.error('Error loading post history:', err);
  }
}

async function loadPostQueue() {
  const tbody = document.getElementById('queueTableBody');
  const countBadge = document.getElementById('queuePendingCount');

  try {
    const res = await fetch('/api/social/queue');
    const data = await res.json();
    if (data.success && data.queue.length > 0) {
      const pendingItems = data.queue.filter(q => q.status === 'pending');
      if (countBadge) countBadge.innerText = pendingItems.length;

      if (tbody) {
        tbody.innerHTML = data.queue.map(item => {
          const imgName = item.card_image_path ? item.card_image_path.split(/[\\/]/).pop() : '';
          const imgWebUrl = `/static/generated/${imgName}`;
          const isVideo = imgName.toLowerCase().endsWith('.mp4');
          const isPending = item.status === 'pending';
          const schedTime = item.scheduled_for ? item.scheduled_for.replace('T', ' ').slice(0, 16) : 'Now';

          return `
            <tr>
              <td>
                <img src="${isVideo ? 'https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=120' : imgWebUrl}" class="rounded border border-secondary" style="width: 60px; height: 60px; object-fit: cover;" onerror="this.src='https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=120'">
              </td>
              <td>
                <div class="fw-bold text-white">${escapeHtml(item.title)}</div>
                <div class="small text-light text-truncate" style="max-width: 350px;">${escapeHtml(item.caption || '')}</div>
              </td>
              <td>
                <span class="badge bg-dark border border-secondary text-white"><i class="fa-brands fa-facebook text-primary me-1"></i>${item.platform || 'facebook'}</span>
              </td>
              <td class="small text-warning fw-bold">
                <i class="fa-regular fa-clock me-1"></i>${schedTime}
              </td>
              <td>
                <span class="badge ${isPending ? 'bg-warning text-dark' : (item.status === 'published' ? 'bg-success' : 'bg-secondary')} fw-bold">
                  ${(item.status || 'pending').toUpperCase()}
                </span>
              </td>
              <td>
                <div class="btn-group btn-group-sm">
                  ${isPending ? `<button class="btn btn-outline-success text-white" onclick="publishQueueItemNow(${item.id})" title="Publish Now Without Waiting"><i class="fa-solid fa-play"></i></button>` : ''}
                  <button class="btn btn-outline-danger text-white" onclick="deleteQueueItem(${item.id})" title="Remove from Queue"><i class="fa-solid fa-trash"></i></button>
                </div>
              </td>
            </tr>
          `;
        }).join('');
      }
    } else {
      if (countBadge) countBadge.innerText = '0';
      if (tbody) tbody.innerHTML = `<tr><td colspan="6" class="text-center text-white py-4">No pending items in queue. All posts are published or newsroom is idle.</td></tr>`;
    }
  } catch (err) {
    console.error('Error loading queue:', err);
  }
}

async function publishQueueItemNow(itemId) {
  showToast('Publishing...', `Publishing queue item #${itemId} now...`);
  try {
    const res = await fetch(`/api/social/queue/publish-now/${itemId}`, { method: 'POST' });
    const data = await res.json();
    if (data.success && data.result.success) {
      showToast('Published!', data.result.message || 'Queued post published successfully!');
    } else {
      showToast('Queue Notice', data.result.message || data.result.error || 'Failed to publish immediately.', false);
    }
    loadPostQueue();
    loadPostHistory();
    loadMetaRateLimitStatus();
  } catch (err) {
    showToast('Error', 'Failed to publish queued item: ' + err.message, false);
  }
}

async function deleteQueueItem(itemId) {
  if (!confirm('Are you sure you want to remove this item from the publishing queue?')) return;
  try {
    const res = await fetch(`/api/social/queue/${itemId}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      showToast('Removed', 'Queue item removed.');
      loadPostQueue();
    }
  } catch (err) {
    showToast('Error', 'Failed to delete queue item.', false);
  }
}

async function loadMetaRateLimitStatus() {
  try {
    const res = await fetch('/api/social/rate-limit-status');
    const data = await res.json();
    if (data.success && data.meta) {
      const meta = data.meta;
      const healthBadge = document.getElementById('metaHealthBadge');
      const progressBar = document.getElementById('metaUsageProgressBar');
      const cooldownInfo = document.getElementById('metaCooldownInfo');
      const lastCheckedTime = document.getElementById('metaLastCheckedTime');
      const queueMetaBadge = document.getElementById('queueMetaStatusBadge');
      const queueCooldownNote = document.getElementById('queueCooldownNote');

      const pct = meta.last_call_count || 0;

      if (meta.token_status === 'expired') {
        if (healthBadge) {
          healthBadge.className = 'badge bg-danger';
          healthBadge.innerText = 'Token Expired';
        }
        if (queueMetaBadge) {
          queueMetaBadge.className = 'text-danger fw-bold mb-1';
          queueMetaBadge.innerText = 'Token Expired';
        }
        if (progressBar) {
          progressBar.style.width = '100%';
          progressBar.className = 'progress-bar bg-danger';
        }
        const msg = '<span class="text-danger fw-bold"><i class="fa-solid fa-circle-exclamation me-1"></i> Page Access Token Expired. Please paste a fresh Page Token below.</span>';
        if (cooldownInfo) cooldownInfo.innerHTML = msg;
        if (queueCooldownNote) queueCooldownNote.innerHTML = '<span class="text-danger fw-bold">Posting Paused (Token Expired)</span>';
      } else if (meta.token_status === 'error') {
        if (healthBadge) {
          healthBadge.className = 'badge bg-danger';
          healthBadge.innerText = 'Auth Error';
        }
        if (progressBar) {
          progressBar.style.width = '100%';
          progressBar.className = 'progress-bar bg-danger';
        }
        const msg = `<span class="text-danger fw-bold"><i class="fa-solid fa-triangle-exclamation me-1"></i> ${meta.token_error || 'Facebook Auth Error'}</span>`;
        if (cooldownInfo) cooldownInfo.innerHTML = msg;
      } else {
        if (healthBadge) {
          healthBadge.className = `badge bg-${meta.status_color}`;
          healthBadge.innerText = meta.status_label;
        }
        if (queueMetaBadge) {
          queueMetaBadge.className = `text-${meta.status_color} fw-bold mb-1`;
          queueMetaBadge.innerText = meta.status_label;
        }
        if (progressBar) {
          progressBar.style.width = `${Math.min(100, pct)}%`;
          progressBar.className = `progress-bar bg-${meta.status_color}`;
        }
        if (meta.in_cooldown) {
          const msg = `Rate Limit Protection Active: Resuming in ${meta.cooldown_remaining_mins}m.`;
          if (cooldownInfo) cooldownInfo.innerText = msg;
          if (queueCooldownNote) queueCooldownNote.innerText = msg;
        } else {
          const msg = `Usage: ${pct}% of Meta hourly quota. System safe.`;
          if (cooldownInfo) cooldownInfo.innerText = msg;
          if (queueCooldownNote) queueCooldownNote.innerText = 'Safe to post without throttling';
        }
      }

      if (lastCheckedTime && meta.last_checked) {
        lastCheckedTime.innerText = 'Checked: ' + meta.last_checked.slice(11, 19);
      }
    }
  } catch (err) {
    console.error('Error checking Meta rate limit status:', err);
  }
}


// ==========================================
// 8. CITY SELECTION MODAL
// ==========================================
function chooseCityQuick(city) {
  document.getElementById('customCityInput').value = city;
  saveCustomCity();
}

async function saveCustomCity() {
  const city = document.getElementById('customCityInput').value.trim() || 'Lahore';
  appState.currentCity = city;
  document.getElementById('currentLocalCity').innerText = city;

  await fetch('/api/settings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ settings: { local_city: city } })
  });

  const modalEl = document.getElementById('cityModal');
  const modal = bootstrap.Modal.getInstance(modalEl);
  if (modal) modal.hide();

  showToast('City Updated', `Local news target set to ${city}`);
  
  if (appState.currentCategory === 'local') {
    loadNewsFeed('local', null, true);
  }
}

function quickSharePost(artId) {
  openInStudio(artId);
  showToast('Opened in Studio', 'Review the card and click "Post to FB Page" or "Download PNG"!');
}

// Quick Video Generation from news feed card
function quickGenerateVideo(artId) {
  const art = appState.articles.find(a => a.id === artId);
  if (!art) { showToast('Article not found', 'danger'); return; }
  window.studioArticle = art;
  generateShortVideo();
}
