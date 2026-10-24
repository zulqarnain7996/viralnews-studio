/**
 * ViralNews Studio - Real-Time HTML5 Canvas Graphic Engine
 * Generates viral 1080p Facebook & TikTok news cards with 14 Themes + Full Urdu RTL
 */

const THEMES = {
  breaking_red: {
    layout: 'classic',
    headerBg: '#dc143c',
    headerText: '#ffffff',
    accent: '#ffd700',
    badgeBg: '#b4001e',
    badgeText: '#ffffff',
    headlineColor: '#ffffff',
    boxBg: 'rgba(15, 17, 23, 0.92)',
    footerBg: '#c80f2d'
  },
  pakistan_green: {
    layout: 'classic',
    headerBg: '#01411c',
    headerText: '#ffffff',
    accent: '#ffffff',
    badgeBg: '#008037',
    badgeText: '#ffffff',
    headlineColor: '#ffffff',
    boxBg: 'rgba(5, 35, 15, 0.94)',
    footerBg: '#01411c'
  },
  viral_dark: {
    layout: 'classic',
    headerBg: '#141821',
    headerText: '#ffffff',
    accent: '#00e5ff',
    badgeBg: '#00b4d8',
    badgeText: '#000000',
    headlineColor: '#ffffff',
    boxBg: 'rgba(10, 12, 18, 0.94)',
    footerBg: '#0f1219'
  },
  royal_blue: {
    layout: 'classic',
    headerBg: '#0a3871',
    headerText: '#ffffff',
    accent: '#ffcc00',
    badgeBg: '#1565c0',
    badgeText: '#ffffff',
    headlineColor: '#ffffff',
    boxBg: 'rgba(8, 22, 44, 0.94)',
    footerBg: '#0a3871'
  },
  buzz_yellow: {
    layout: 'classic',
    headerBg: '#ffcc00',
    headerText: '#000000',
    accent: '#dc143c',
    badgeBg: '#000000',
    badgeText: '#ffcc00',
    headlineColor: '#ffffff',
    boxBg: 'rgba(18, 18, 18, 0.94)',
    footerBg: '#ffcc00',
    footerText: '#000000'
  },
  editorial_purple: {
    layout: 'classic',
    headerBg: '#4a154b',
    headerText: '#ffffff',
    accent: '#e01e5a',
    badgeBg: '#6e1e73',
    badgeText: '#ffffff',
    headlineColor: '#ffffff',
    boxBg: 'rgba(25, 10, 28, 0.94)',
    footerBg: '#4a154b'
  },
  quote_card: {
    layout: 'classic',
    headerBg: '#1e232d',
    headerText: '#ffffff',
    accent: '#3b82f6',
    badgeBg: '#2563eb',
    badgeText: '#ffffff',
    headlineColor: '#ffffff',
    boxBg: 'rgba(15, 18, 24, 0.95)',
    footerBg: '#181c26'
  },
  urdu_khabarnama: {
    layout: 'classic',
    headerBg: '#be0000',
    headerText: '#ffffff',
    accent: '#ffffff',
    badgeBg: '#ffd700',
    badgeText: '#a00000',
    headlineColor: '#ffffff',
    boxBg: 'rgba(12, 12, 16, 0.95)',
    footerBg: '#be0000'
  },
  turkiye_urdu_split: {
    layout: 'turkiye',
    bottomBg: '#a5000a',
    accent: '#ffd700',
    logoBg: '#a5000a',
    headlineColor: '#ffd700',
    footerBg: '#780007',
    badgeText: '#ffd700'
  },
  turkiye_emerald_split: {
    layout: 'turkiye',
    bottomBg: '#014b20',
    accent: '#ffd700',
    logoBg: '#014b20',
    headlineColor: '#ffd700',
    footerBg: '#003214',
    badgeText: '#ffffff'
  },
  turkiye_dark_split: {
    layout: 'turkiye',
    bottomBg: '#161923',
    accent: '#00f0ff',
    logoBg: '#161923',
    headlineColor: '#00f0ff',
    footerBg: '#0e1017',
    badgeText: '#00f0ff'
  },
  dw_quote_blue: {
    layout: 'dw_quote',
    bg: '#0096e6',
    quoteColor: '#002855',
    headlineColor: '#00234b',
    summaryColor: '#003575',
    logoBg: '#00234b',
    footerBg: '#007bbd'
  },
  dw_quote_dark: {
    layout: 'dw_quote',
    bg: '#12161e',
    quoteColor: '#00f0ff',
    headlineColor: '#ffffff',
    summaryColor: '#cbd5e1',
    logoBg: '#00f0ff',
    logoText: '#000000',
    footerBg: '#0c0f14'
  },
  dw_quote_red: {
    layout: 'dw_quote',
    bg: '#b40a19',
    quoteColor: '#ffd700',
    headlineColor: '#ffffff',
    summaryColor: '#ffea75',
    logoBg: '#780007',
    footerBg: '#820510'
  },
  neon_cyber_split: {
    layout: 'neon_cyber_split',
    bottomBg: '#090d16',
    accent: '#00f0ff',
    logoBg: '#001a26',
    headlineColor: '#ffffff',
    footerBg: '#04070c',
    badgeBg: '#00f0ff',
    badgeText: '#000000'
  },
  royal_gold_split: {
    layout: 'royal_gold_split',
    bottomBg: '#360008',
    accent: '#ffd700',
    logoBg: '#2a0006',
    headlineColor: '#ffd700',
    footerBg: '#1f0004',
    badgeBg: '#ffd700',
    badgeText: '#000000'
  },
  vox_spotlight_dark: {
    layout: 'vox_spotlight',
    bottomBg: '#0d0f14',
    accent: '#ccff00',
    logoBg: '#181b22',
    headlineColor: '#ffffff',
    footerBg: '#08090c',
    badgeBg: '#ccff00',
    badgeText: '#000000'
  },
  ticker_live_tv: {
    layout: 'ticker_tv',
    tickerBg: '#cc0010',
    bottomBg: '#0b1220',
    accent: '#ff2035',
    logoBg: 'rgba(0,0,0,0.7)',
    headlineColor: '#ffffff',
    footerBg: '#060a12'
  },
  cinematic_letterbox: {
    layout: 'cinematic_letterbox',
    barBg: '#000000',
    accent: '#ff1e38',
    headlineColor: '#ffffff',
    badgeBg: '#ff1e38'
  }
};

const THEMATIC_BACKDROPS = {
  breaking: 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=1080&auto=format&fit=crop&q=80',
  pakistan: 'https://images.unsplash.com/photo-1588691090382-747209ee6e06?w=1080&auto=format&fit=crop&q=80',
  military: 'https://images.unsplash.com/photo-1541872703-74c5e44368f9?w=1080&auto=format&fit=crop&q=80',
  politics: 'https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?w=1080&auto=format&fit=crop&q=80',
  sports: 'https://images.unsplash.com/photo-1531415074868-83633dd5e45c?w=1080&auto=format&fit=crop&q=80',
  economy: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1080&auto=format&fit=crop&q=80',
  court: 'https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=1080&auto=format&fit=crop&q=80',
  world: 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1080&auto=format&fit=crop&q=80'
};

let currentStudioState = {
  theme: 'turkiye_urdu_split',
  aspectRatio: '1:1',
  tag: '🔴 بریکنگ نیوز',
  pageName: 'PAK NEWS 24/7',
  title: 'دہشت گرد جہاں بھی موجود ہوں گے، انہیں سخت جواب دیا جائے گا، فیلڈ مارشل',
  summary: 'اسپانسرڈ دہشت گرد تنظیموں کے خلاف مہم کو بھرپور طریقے سے جاری رکھیں گے، آرمی چیف',
  source: 'EXPRESS NEWS',
  handle: '@PakNewsOfficial',
  imageUrl: THEMATIC_BACKDROPS.military,
  fontSize: 52,
  headlineColor: null, // null means use theme default
  textAlign: 'auto',   // 'auto', 'right', 'center', 'left'
  overlayDarkness: 0,  // 0 to 70%
  loadedImg: null
};

let canvas = null;
let ctx = null;

function isUrduText(text) {
  return /[\u0600-\u06FF]/.test(text || '');
}

function decodeHtmlEntities(str) {
  if (!str) return '';
  const txt = document.createElement("textarea");
  txt.innerHTML = str;
  return txt.value.replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim();
}

function initCanvasStudio() {
  canvas = document.getElementById('newsCanvas');
  if (!canvas) return;
  ctx = canvas.getContext('2d');
  
  loadImageObject(currentStudioState.imageUrl, () => {
    renderStudioCanvas();
  });
}

function loadImageObject(url, callback) {
  if (!url) return;

  // Route external images through CORS proxy for Canvas compatibility & full 1080p resolution
  const isExternalHttp = (url.startsWith('http://') || url.startsWith('https://')) &&
    !url.includes(window.location.host) &&
    !url.includes('127.0.0.1:8000') &&
    !url.includes('localhost:8000');

  const proxyUrl = isExternalHttp
    ? `/api/cards/proxy-image?url=${encodeURIComponent(url)}`
    : url;

  const img = new Image();
  img.crossOrigin = 'anonymous';
  img.onload = () => {
    currentStudioState.loadedImg = img;
    if (callback) callback();
  };
  img.onerror = () => {
    console.warn('Image load error for:', proxyUrl, 'trying direct or fallback');
    if (proxyUrl !== url) {
      const direct = new Image();
      direct.crossOrigin = 'anonymous';
      direct.onload = () => {
        currentStudioState.loadedImg = direct;
        if (callback) callback();
      };
      direct.onerror = () => {
        loadFallbackImg(callback);
      };
      direct.src = url;
    } else {
      loadFallbackImg(callback);
    }
  };
  img.src = proxyUrl;
}

function loadFallbackImg(callback) {
  const fallback = new Image();
  fallback.crossOrigin = 'anonymous';
  fallback.onload = () => {
    currentStudioState.loadedImg = fallback;
    if (callback) callback();
  };
  fallback.src = THEMATIC_BACKDROPS.breaking;
}

function setStudioTheme(themeKey) {
  if (!THEMES[themeKey]) return;
  currentStudioState.theme = themeKey;
  
  document.querySelectorAll('.theme-btn').forEach(btn => {
    btn.classList.remove('active');
    const badge = btn.querySelector('.theme-active-check');
    if (badge) badge.remove();
  });

  const targetBtn = document.querySelector(`[data-theme="${themeKey}"]`);
  if (targetBtn) {
    targetBtn.classList.add('active');
    const badge = document.createElement('span');
    badge.className = 'theme-active-check badge bg-info text-dark ms-auto py-1 px-1';
    badge.innerText = '✓';
    targetBtn.appendChild(badge);
  }
  
  renderStudioCanvas();
}

function setHeadlineColor(color) {
  currentStudioState.headlineColor = color;
  document.querySelectorAll('.headline-color-btn').forEach(b => b.classList.remove('active'));
  const btn = document.querySelector(`[data-headline-color="${color}"]`);
  if (btn) btn.classList.add('active');
  renderStudioCanvas();
}

function setHeadlineAlign(align) {
  currentStudioState.textAlign = align;
  document.querySelectorAll('.headline-align-btn').forEach(b => b.classList.remove('active'));
  const btn = document.querySelector(`[data-headline-align="${align}"]`);
  if (btn) btn.classList.add('active');
  renderStudioCanvas();
}

function setPhotoDarkness(val) {
  currentStudioState.overlayDarkness = parseInt(val) || 0;
  const label = document.getElementById('studioDarknessVal');
  if (label) label.innerText = `${currentStudioState.overlayDarkness}%`;
  renderStudioCanvas();
}

function setStudioRatio(ratio) {
  currentStudioState.aspectRatio = ratio;
  const isVertical = (ratio === '9:16');
  
  const squareBtn = document.getElementById('btnRatioSquare');
  const vertBtn = document.getElementById('btnRatioVertical');
  if (squareBtn && vertBtn) {
    if (isVertical) {
      vertBtn.classList.add('active');
      squareBtn.classList.remove('active');
    } else {
      squareBtn.classList.add('active');
      vertBtn.classList.remove('active');
    }
  }

  if (canvas) {
    if (isVertical) {
      canvas.width = 1080;
      canvas.height = 1920;
    } else {
      canvas.width = 1080;
      canvas.height = 1080;
    }
  }

  renderStudioCanvas();
}

function setStudioBackdrop(type) {
  if (THEMATIC_BACKDROPS[type]) {
    loadStudioImage(THEMATIC_BACKDROPS[type]);
  }
}

function useThematicBackdrop(type) {
  setStudioBackdrop(type);
}

function loadStudioImage(url) {
  currentStudioState.imageUrl = url;
  const bgInput = document.getElementById('studioImageUrlInput') || document.getElementById('studioBgUrlInput');
  if (bgInput) bgInput.value = url;
  
  loadImageObject(url, () => {
    renderStudioCanvas();
  });
}

function triggerCustomPhotoUpload() {
  const fileInput = document.getElementById('studioCustomFileInput');
  if (fileInput) fileInput.click();
}

function handleCustomPhotoUpload(fileInput) {
  if (!fileInput.files || !fileInput.files[0]) return;
  const file = fileInput.files[0];
  const reader = new FileReader();
  reader.onload = (e) => {
    loadStudioImage(e.target.result);
  };
  reader.readAsDataURL(file);
}

function transformHeadlineCase() {
  const titleInput = document.getElementById('studioTitleInput');
  if (!titleInput) return;
  const val = titleInput.value;
  if (isUrduText(val)) return; // Urdu has no case
  if (val === val.toUpperCase()) {
    titleInput.value = val.toLowerCase().replace(/\b\w/g, s => s.toUpperCase());
  } else {
    titleInput.value = val.toUpperCase();
  }
  renderStudioCanvas();
}

// Text wrapping utility for HTML5 Canvas
function wrapText(context, text, maxWidth) {
  if (!text) return [];
  const words = text.split(/\s+/);
  const lines = [];
  let currentLine = words[0] || '';

  for (let i = 1; i < words.length; i++) {
    const word = words[i];
    const testLine = currentLine + ' ' + word;
    const width = context.measureText(testLine).width;
    if (width < maxWidth) {
      currentLine = testLine;
    } else {
      lines.push(currentLine);
      currentLine = word;
    }
  }
  if (currentLine) {
    lines.push(currentLine);
  }
  return lines;
}

// ========================================================
// MAIN STUDIO CANVAS DISPATCHER
// ========================================================
function renderStudioCanvas() {
  if (!canvas || !ctx) return;

  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';

  const width = canvas.width;
  const height = canvas.height;
  const theme = THEMES[currentStudioState.theme] || THEMES.turkiye_urdu_split;

  // Read current input values & clean entities
  const rawPageName = document.getElementById('studioPageNameInput')?.value || currentStudioState.pageName;
  const pageName = decodeHtmlEntities(rawPageName);

  const rawTag = document.getElementById('studioTagInput')?.value || currentStudioState.tag;
  const categoryTag = decodeHtmlEntities(rawTag);

  const rawTitle = document.getElementById('studioTitleInput')?.value || currentStudioState.title;
  const title = decodeHtmlEntities(rawTitle);

  const rawSummary = document.getElementById('studioSummaryInput')?.value || currentStudioState.summary;
  const summary = decodeHtmlEntities(rawSummary);

  const rawSource = document.getElementById('studioSourceInput')?.value || currentStudioState.source;
  const source = decodeHtmlEntities(rawSource).toUpperCase();

  const handle = document.getElementById('studioHandleInput')?.value || currentStudioState.handle;
  const fontSize = parseInt(document.getElementById('studioFontSize')?.value || currentStudioState.fontSize);
  
  const isUrdu = isUrduText(title);

  const sizeValLabel = document.getElementById('studioFontSizeVal');
  if (sizeValLabel) sizeValLabel.innerText = `${fontSize}px`;

  // Dispatch to the matching template layout engine
  if (theme.layout === 'turkiye') {
    renderTurkiyeSplitLayout(theme, width, height, pageName, categoryTag, title, summary, source, handle, fontSize, isUrdu);
  } else if (theme.layout === 'dw_quote') {
    renderDWQuoteLayout(theme, width, height, pageName, categoryTag, title, summary, source, handle, fontSize, isUrdu);
  } else if (theme.layout === 'neon_cyber_split') {
    renderNeonCyberSplitLayout(theme, width, height, pageName, categoryTag, title, summary, source, handle, fontSize, isUrdu);
  } else if (theme.layout === 'royal_gold_split') {
    renderRoyalGoldSplitLayout(theme, width, height, pageName, categoryTag, title, summary, source, handle, fontSize, isUrdu);
  } else if (theme.layout === 'vox_spotlight') {
    renderVoxSpotlightLayout(theme, width, height, pageName, categoryTag, title, summary, source, handle, fontSize, isUrdu);
  } else if (theme.layout === 'ticker_tv') {
    renderTickerTVLayout(theme, width, height, pageName, categoryTag, title, summary, source, handle, fontSize, isUrdu);
  } else if (theme.layout === 'cinematic_letterbox') {
    renderCinematicLetterboxLayout(theme, width, height, pageName, categoryTag, title, summary, source, handle, fontSize, isUrdu);
  } else {
    renderClassicBroadcastLayout(theme, width, height, pageName, categoryTag, title, summary, source, handle, fontSize, isUrdu);
  }
}

// ========================================================
// 1. TURKIYE URDU SPLIT LAYOUT (Screenshots 1 & 2)
// ========================================================
function renderTurkiyeSplitLayout(theme, width, height, pageName, categoryTag, title, summary, source, handle, fontSize, isUrdu) {
  const splitY = Math.floor(height * 0.52);

  // 1. Clear background
  ctx.fillStyle = '#0f1117';
  ctx.fillRect(0, 0, width, height);

  // 2. Top Half: Photo with aspect fill
  if (currentStudioState.loadedImg) {
    const img = currentStudioState.loadedImg;
    const targetH = splitY;
    const imgRatio = img.width / img.height;
    const targetRatio = width / targetH;
    let renderW, renderH, cropX, cropY;

    if (imgRatio > targetRatio) {
      renderH = targetH;
      renderW = targetH * imgRatio;
      cropX = (renderW - width) / 2;
      cropY = 0;
    } else {
      renderW = width;
      renderH = width / imgRatio;
      cropX = 0;
      cropY = (renderH - targetH) / 2;
    }
    ctx.drawImage(img, -cropX, -cropY, renderW, renderH);
  } else {
    ctx.fillStyle = '#1e2330';
    ctx.fillRect(0, 0, width, splitY);
  }

  // Darkness overlay on photo if configured
  if (currentStudioState.overlayDarkness > 0) {
    ctx.fillStyle = `rgba(0, 0, 0, ${currentStudioState.overlayDarkness / 100})`;
    ctx.fillRect(0, 0, width, splitY);
  }

  // Top-left Logo Box (White border with theme fill)
  const logoW = 200;
  const logoH = 75;
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(25, 25, logoW, logoH);
  ctx.fillStyle = theme.logoBg || '#a5000a';
  ctx.fillRect(30, 30, logoW - 10, logoH - 10);

  ctx.font = isUrduText(pageName) 
    ? '800 24px "Noto Sans Arabic", "Noto Nastaliq Urdu", sans-serif'
    : '900 26px "Montserrat", "Impact", sans-serif';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(pageName, 25 + logoW / 2, 25 + logoH / 2);

  // Top-right Red LIVE Badge
  const liveW = 90;
  const liveH = 40;
  const liveX = width - liveW - 25;
  const liveY = 25;
  ctx.fillStyle = '#ff0000';
  ctx.fillRect(liveX, liveY, liveW, liveH);
  ctx.lineWidth = 2;
  ctx.strokeStyle = '#ffffff';
  ctx.strokeRect(liveX, liveY, liveW, liveH);
  ctx.font = '700 20px "Inter", sans-serif';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'center';
  ctx.fillText('LIVE', liveX + liveW / 2, liveY + liveH / 2);

  // 3. Bottom Half: Crimson Red / Emerald / Dark Background
  ctx.fillStyle = theme.bottomBg || '#a5000a';
  ctx.fillRect(0, splitY, width, height - splitY);

  // Shadow seam along the split
  const seamGrad = ctx.createLinearGradient(0, splitY, 0, splitY + 16);
  seamGrad.addColorStop(0, 'rgba(0, 0, 0, 0.7)');
  seamGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
  ctx.fillStyle = seamGrad;
  ctx.fillRect(0, splitY, width, 16);

  // 4. Headline Text (Centred, Bold Golden Yellow)
  const headlineFont = isUrdu
    ? `800 ${fontSize}px "Noto Sans Arabic", "Noto Nastaliq Urdu", 'Segoe UI', sans-serif`
    : `900 ${fontSize}px "Impact", "Montserrat", sans-serif`;
  ctx.font = headlineFont;

  const maxTextW = width - 100;
  const headlineLines = wrapText(ctx, title, maxTextW).slice(0, 3);
  const lineH = Math.floor(fontSize * 1.55);

  const fontSummary = isUrdu
    ? '700 26px "Noto Sans Arabic", "Noto Nastaliq Urdu", sans-serif'
    : '600 24px "Inter", sans-serif';
  ctx.font = fontSummary;
  const summaryLines = summary ? wrapText(ctx, summary, maxTextW).slice(0, 2) : [];
  const summaryLineH = 38;

  const totalTextH = (headlineLines.length * lineH) + (summaryLines.length > 0 ? (summaryLines.length * summaryLineH + 20) : 0);
  const availableBottomH = height - splitY - 80;
  let curY = splitY + Math.max(30, Math.floor((availableBottomH - totalTextH) / 2)) + Math.floor(fontSize * 0.75);

  // Draw Headline Lines
  ctx.font = headlineFont;
  const align = currentStudioState.textAlign === 'auto' ? 'center' : currentStudioState.textAlign;
  ctx.textAlign = align;
  let textX = width / 2;
  if (align === 'right') textX = width - 60;
  if (align === 'left') textX = 60;

  const hlColor = currentStudioState.headlineColor || theme.headlineColor || '#ffd700';

  headlineLines.forEach(line => {
    // Drop shadow
    ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
    ctx.fillText(line, textX + 3, curY + 3);
    // Main text
    ctx.fillStyle = hlColor;
    ctx.fillText(line, textX, curY);
    curY += lineH;
  });

  // Draw Summary
  if (summaryLines.length > 0) {
    curY += 8;
    ctx.font = fontSummary;
    ctx.textAlign = 'center';
    summaryLines.forEach(sLine => {
      ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
      ctx.fillText(sLine, width / 2, curY);
      curY += summaryLineH;
    });
  }

  // 5. Footer Bar
  const footerY = height - 65;
  // Bottom-left: Website badge
  const badgeW = 260;
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(25, footerY, badgeW, 42);
  ctx.lineWidth = 1;
  ctx.strokeStyle = '#cccccc';
  ctx.strokeRect(25, footerY, badgeW, 42);
  ctx.font = '700 20px "Inter", sans-serif';
  ctx.fillStyle = '#a5000a';
  ctx.textAlign = 'left';
  ctx.fillText(`➤ ${pageName.toLowerCase().replace(/[^a-z0-9]/g, '')}.pk`, 38, footerY + 28);

  // Bottom-right: Social Handle
  ctx.font = '700 22px "Inter", sans-serif';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'right';
  ctx.fillText(`𝕏 f 📷  ${handle}`, width - 30, footerY + 28);
}

// ========================================================
// 2. DW URDU QUOTE CARD LAYOUT
// ========================================================
function renderDWQuoteLayout(theme, width, height, pageName, categoryTag, title, summary, source, handle, fontSize, isUrdu) {
  // 1. Background fill
  ctx.fillStyle = theme.bg || '#0096e6';
  ctx.fillRect(0, 0, width, height);

  // 2. Top Rectangular News Photo (~44% of card) with margins
  const photoMargin = 30;
  const photoW = width - (photoMargin * 2);
  const photoH = Math.floor(height * 0.44);

  if (currentStudioState.loadedImg) {
    const img = currentStudioState.loadedImg;
    const imgRatio = img.width / img.height;
    const targetRatio = photoW / photoH;
    let renderW, renderH, cropX, cropY;

    if (imgRatio > targetRatio) {
      renderH = photoH;
      renderW = photoH * imgRatio;
      cropX = (renderW - photoW) / 2;
      cropY = 0;
    } else {
      renderW = photoW;
      renderH = photoW / imgRatio;
      cropX = 0;
      cropY = (renderH - photoH) / 2;
    }

    ctx.save();
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(photoMargin, photoMargin, photoW, photoH, 8) : ctx.rect(photoMargin, photoMargin, photoW, photoH);
    ctx.clip();
    ctx.drawImage(img, photoMargin - cropX, photoMargin - cropY, renderW, renderH);
    ctx.restore();
  }

  // DW Page Brand Pill on Top-Left of Photo
  const pillW = 180;
  const pillH = 50;
  ctx.fillStyle = theme.logoBg || '#00234b';
  ctx.fillRect(photoMargin + 15, photoMargin + 15, pillW, pillH);
  ctx.font = '800 22px "Inter", sans-serif';
  ctx.fillStyle = theme.logoText || '#ffffff';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(pageName.toUpperCase(), photoMargin + 15 + pillW / 2, photoMargin + 15 + pillH / 2);

  // 3. Bottom Half: Massive Quotation Mark + Quote Text
  const quoteStartY = photoMargin + photoH + 20;
  
  // Draw Quotation Marks
  ctx.font = '900 85px "Georgia", serif';
  ctx.fillStyle = theme.quoteColor || '#002855';
  ctx.textAlign = isUrdu ? 'right' : 'left';
  const quoteX = isUrdu ? width - 40 : 45;
  ctx.fillText('“', quoteX, quoteStartY + 45);

  // Headline Text
  const quoteFont = isUrdu
    ? `800 ${fontSize}px "Noto Sans Arabic", "Noto Nastaliq Urdu", sans-serif`
    : `800 ${fontSize}px "Inter", sans-serif`;
  ctx.font = quoteFont;

  const maxTextW = width - 120;
  const headlineLines = wrapText(ctx, title, maxTextW).slice(0, 4);
  const lineH = Math.floor(fontSize * 1.55);

  let curY = quoteStartY + 75;
  ctx.textAlign = isUrdu ? 'right' : 'left';
  const textX = isUrdu ? width - 50 : 50;

  headlineLines.forEach(line => {
    ctx.fillStyle = theme.headlineColor || '#00234b';
    ctx.fillText(line, textX, curY);
    curY += lineH;
  });

  // Summary / Speaker attribution
  if (summary) {
    curY += 10;
    ctx.font = isUrdu 
      ? '700 24px "Noto Sans Arabic", "Noto Nastaliq Urdu", sans-serif'
      : '600 24px "Inter", sans-serif';
    ctx.fillStyle = theme.summaryColor || '#003575';
    const summaryLines = wrapText(ctx, summary, maxTextW).slice(0, 2);
    summaryLines.forEach(sLine => {
      ctx.fillText(sLine, textX, curY);
      curY += 34;
    });
  }

  // 4. Footer Bar
  const footerH = 60;
  const footerY = height - footerH;
  ctx.fillStyle = theme.footerBg || '#007bbd';
  ctx.fillRect(0, footerY, width, footerH);

  ctx.font = isUrdu ? '700 22px "Noto Sans Arabic", sans-serif' : '700 22px "Inter", sans-serif';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.fillText(`ذرائع: ${source}`, 35, footerY + footerH / 2);

  ctx.textAlign = 'right';
  ctx.fillText(`Follow ${handle}`, width - 35, footerY + footerH / 2);
}

// ========================================================
// 3. CLASSIC BROADCAST THEMES (8 Classic Templates)
// ========================================================
function renderClassicBroadcastLayout(theme, width, height, pageName, categoryTag, title, summary, source, handle, fontSize, isUrdu) {
  // 1. Hero Background Image (Fill & Cover)
  ctx.fillStyle = '#0a0c10';
  ctx.fillRect(0, 0, width, height);

  if (currentStudioState.loadedImg) {
    const img = currentStudioState.loadedImg;
    const imgRatio = img.width / img.height;
    const canvasRatio = width / height;
    let renderW, renderH, cropX, cropY;

    if (imgRatio > canvasRatio) {
      renderH = height;
      renderW = height * imgRatio;
      cropX = (renderW - width) / 2;
      cropY = 0;
    } else {
      renderW = width;
      renderH = width / imgRatio;
      cropX = 0;
      cropY = (renderH - height) / 2;
    }
    ctx.drawImage(img, -cropX, -cropY, renderW, renderH);
  }

  // Darkness overlay on photo if configured
  if (currentStudioState.overlayDarkness > 0) {
    ctx.fillStyle = `rgba(0, 0, 0, ${currentStudioState.overlayDarkness / 100})`;
    ctx.fillRect(0, 0, width, height);
  }

  // 2. Cinematic Vignette & Bottom Text Gradient
  const topGrad = ctx.createLinearGradient(0, 0, 0, 160);
  topGrad.addColorStop(0, 'rgba(0, 0, 0, 0.75)');
  topGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
  ctx.fillStyle = topGrad;
  ctx.fillRect(0, 0, width, 160);

  const gradStart = height * 0.38;
  const bottomGrad = ctx.createLinearGradient(0, gradStart, 0, height);
  bottomGrad.addColorStop(0, 'rgba(10, 12, 16, 0.05)');
  bottomGrad.addColorStop(0.3, 'rgba(10, 12, 16, 0.70)');
  bottomGrad.addColorStop(0.7, 'rgba(10, 12, 16, 0.96)');
  bottomGrad.addColorStop(1, 'rgba(10, 12, 16, 1.0)');
  ctx.fillStyle = bottomGrad;
  ctx.fillRect(0, gradStart, width, height - gradStart);

  // 3. Header Top Banner
  const headerHeight = 90;
  ctx.fillStyle = theme.headerBg;
  ctx.fillRect(0, 0, width, headerHeight);

  ctx.fillStyle = theme.accent;
  ctx.fillRect(0, headerHeight, width, 6);

  // Header Brand Name
  ctx.font = isUrduText(pageName)
    ? '800 36px "Noto Sans Arabic", "Noto Nastaliq Urdu", sans-serif'
    : '900 42px "Impact", "Montserrat", sans-serif';
  ctx.fillStyle = theme.headerText;
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.fillText(pageName.toUpperCase(), 36, headerHeight / 2);

  // LIVE Pill Badge on top-right
  const liveW = 90;
  const liveH = 40;
  const liveX = width - liveW - 36;
  const liveY = (headerHeight - liveH) / 2;
  ctx.fillStyle = '#ff0000';
  ctx.fillRect(liveX, liveY, liveW, liveH);
  ctx.lineWidth = 2;
  ctx.strokeStyle = '#ffffff';
  ctx.strokeRect(liveX, liveY, liveW, liveH);
  ctx.font = '700 22px "Inter", sans-serif';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'center';
  ctx.fillText('LIVE', liveX + liveW / 2, liveY + liveH / 2);

  // 4. Category Badge
  const badgeY = headerHeight + 30;
  const isUrduBadge = isUrduText(categoryTag);
  ctx.font = isUrduBadge 
    ? '800 28px "Noto Sans Arabic", "Noto Nastaliq Urdu", sans-serif'
    : '900 30px "Impact", "Montserrat", sans-serif';
  
  const tagMetrics = ctx.measureText(categoryTag);
  const tagW = Math.max(tagMetrics.width + 48, 160);
  const tagH = 52;

  ctx.fillStyle = theme.badgeBg;
  ctx.fillRect(36, badgeY, tagW, tagH);
  ctx.lineWidth = 3;
  ctx.strokeStyle = theme.accent;
  ctx.strokeRect(36, badgeY, tagW, tagH);

  ctx.fillStyle = theme.badgeText;
  ctx.textAlign = 'center';
  ctx.fillText(categoryTag, 36 + tagW / 2, badgeY + tagH / 2 + 2);

  // 5. Lower Third Box Calculation
  const footerHeight = 80;
  const contentBottom = height - footerHeight - 30;
  const maxTextWidth = width - 150;

  const headlineFont = isUrdu
    ? `800 ${fontSize}px "Noto Sans Arabic", "Noto Nastaliq Urdu", sans-serif`
    : `900 ${fontSize}px "Impact", "Montserrat", sans-serif`;
  ctx.font = headlineFont;
  const headlineLines = wrapText(ctx, title, maxTextWidth).slice(0, 4);

  const summaryFont = isUrdu
    ? '700 26px "Noto Sans Arabic", "Noto Nastaliq Urdu", sans-serif'
    : '600 26px "Inter", sans-serif';
  ctx.font = summaryFont;
  const summaryLines = summary ? wrapText(ctx, summary, maxTextWidth).slice(0, 3) : [];

  const headlineLineHeight = Math.floor(fontSize * 1.55);
  const summaryLineHeight = 36;
  const totalHeadlineH = headlineLines.length * headlineLineHeight;
  const totalSummaryH = summaryLines.length > 0 ? (summaryLines.length * summaryLineHeight + 25) : 0;

  const boxPad = 28;
  const totalBoxH = totalHeadlineH + totalSummaryH + (boxPad * 2);
  const boxTop = contentBottom - totalBoxH;

  // Draw Frosted Backing Box
  ctx.fillStyle = theme.boxBg;
  ctx.fillRect(30, boxTop, width - 60, totalBoxH);
  ctx.lineWidth = 3;
  ctx.strokeStyle = theme.accent;
  ctx.strokeRect(30, boxTop, width - 60, totalBoxH);

  let curY = boxTop + boxPad + Math.floor(fontSize * 0.75);

  const hlColor = currentStudioState.headlineColor || theme.headlineColor || (isUrdu ? '#ffd700' : '#ffffff');

  if (isUrdu) {
    // URDU RTL
    ctx.fillStyle = theme.accent;
    ctx.fillRect(width - 55, boxTop + boxPad, 8, totalHeadlineH - 8);

    ctx.font = headlineFont;
    const align = currentStudioState.textAlign === 'auto' ? 'right' : currentStudioState.textAlign;
    ctx.textAlign = align;
    let textX = width - 72;
    if (align === 'center') textX = width / 2;
    if (align === 'left') textX = 72;

    headlineLines.forEach(line => {
      ctx.fillStyle = '#000000';
      ctx.fillText(line, textX + 2, curY + 2);
      ctx.fillStyle = hlColor;
      ctx.fillText(line, textX, curY);
      curY += headlineLineHeight;
    });

    if (summaryLines.length > 0) {
      curY += 8;
      ctx.strokeStyle = 'rgba(150, 160, 180, 0.4)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(60, curY - 14);
      ctx.lineTo(width - 60, curY - 14);
      ctx.stroke();

      ctx.font = summaryFont;
      summaryLines.forEach(sLine => {
        ctx.fillStyle = 'rgba(230, 235, 245, 0.95)';
        ctx.fillText(sLine, textX, curY);
        curY += summaryLineHeight;
      });
    }
  } else {
    // ENGLISH LTR
    ctx.fillStyle = theme.accent;
    ctx.fillRect(45, boxTop + boxPad, 8, totalHeadlineH - 8);

    ctx.font = headlineFont;
    const align = currentStudioState.textAlign === 'auto' ? 'left' : currentStudioState.textAlign;
    ctx.textAlign = align;
    let textX = 68;
    if (align === 'center') textX = width / 2;
    if (align === 'right') textX = width - 72;

    headlineLines.forEach(line => {
      ctx.fillStyle = '#000000';
      ctx.fillText(line, textX + 3, curY + 3);
      ctx.fillStyle = hlColor;
      ctx.fillText(line, textX, curY);
      curY += headlineLineHeight;
    });

    if (summaryLines.length > 0) {
      curY += 8;
      ctx.strokeStyle = 'rgba(150, 160, 180, 0.4)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(68, curY - 14);
      ctx.lineTo(width - 60, curY - 14);
      ctx.stroke();

      ctx.font = summaryFont;
      summaryLines.forEach(sLine => {
        ctx.fillStyle = 'rgba(230, 235, 245, 0.95)';
        ctx.fillText(sLine, textX, curY);
        curY += summaryLineHeight;
      });
    }
  }

  // 6. Footer Bar
  const footerTop = height - footerHeight;
  ctx.fillStyle = theme.footerBg;
  ctx.fillRect(0, footerTop, width, footerHeight);

  const footerTextCol = theme.footerText || '#ffffff';
  ctx.font = isUrdu ? '700 24px "Noto Sans Arabic", sans-serif' : '700 24px "Inter", sans-serif';
  ctx.fillStyle = footerTextCol;
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  const sourceLabel = isUrdu ? `ذرائع: ${source}` : `SOURCE: ${source}`;
  ctx.fillText(sourceLabel, 36, footerTop + footerHeight / 2);

  ctx.font = '700 24px "Inter", sans-serif';
  ctx.fillStyle = theme.accent;
  ctx.textAlign = 'right';
  ctx.fillText(`Follow ${handle}`, width - 36, footerTop + footerHeight / 2);
}

// ========================================================
// HELPER: DRAW FITTED HORIZONTAL PHOTO (PREVENTS ZOOM / HEAD CROPPING)
// ========================================================
function drawFittedPhoto(context, img, x, y, w, h) {
  if (!img) {
    context.fillStyle = '#161922';
    context.fillRect(x, y, w, h);
    return;
  }
  const imgRatio = img.width / img.height;
  const targetRatio = w / h;
  let renderW, renderH, cropX, cropY;

  if (imgRatio > targetRatio) {
    renderH = h;
    renderW = h * imgRatio;
    cropX = (renderW - w) / 2;
    cropY = 0;
  } else {
    renderW = w;
    renderH = w / imgRatio;
    cropX = 0;
    cropY = (renderH - h) / 2;
  }
  context.save();
  context.beginPath();
  context.rect(x, y, w, h);
  context.clip();
  context.drawImage(img, x - cropX, y - cropY, renderW, renderH);
  context.restore();
}

// ========================================================
// 4. NEON CYBER BROADCAST PRO (Ultra-Modern High Tech)
// ========================================================
function renderNeonCyberSplitLayout(theme, width, height, pageName, categoryTag, title, summary, source, handle, fontSize, isUrdu) {
  const splitY = Math.floor(height * 0.52);
  const cyan = '#00f0ff';
  const darkBg = '#070a12';

  // 1. Background
  ctx.fillStyle = darkBg;
  ctx.fillRect(0, 0, width, height);

  // 2. Photo (Fit in top 52% - NO image distortion/zoom)
  drawFittedPhoto(ctx, currentStudioState.loadedImg, 0, 0, width, splitY);

  if (currentStudioState.overlayDarkness > 0) {
    ctx.fillStyle = `rgba(0, 0, 0, ${currentStudioState.overlayDarkness / 100})`;
    ctx.fillRect(0, 0, width, splitY);
  }

  // Top gradient shadow on photo
  const photoTopGrad = ctx.createLinearGradient(0, 0, 0, 110);
  photoTopGrad.addColorStop(0, 'rgba(0, 0, 0, 0.85)');
  photoTopGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');
  ctx.fillStyle = photoTopGrad;
  ctx.fillRect(0, 0, width, 110);

  // Cyber Corner Brackets on Photo
  ctx.strokeStyle = cyan;
  ctx.lineWidth = 3;
  // Top-Left bracket
  ctx.beginPath();
  ctx.moveTo(15, 45); ctx.lineTo(15, 15); ctx.lineTo(45, 15);
  ctx.stroke();
  // Top-Right bracket
  ctx.beginPath();
  ctx.moveTo(width - 45, 15); ctx.lineTo(width - 15, 15); ctx.lineTo(width - 15, 45);
  ctx.stroke();

  // Channel Logo Pill (Top-Left)
  const pillW = Math.max(220, ctx.measureText(pageName).width + 60);
  const pillH = 54;
  ctx.fillStyle = 'rgba(6, 12, 24, 0.9)';
  ctx.fillRect(35, 25, pillW, pillH);
  ctx.lineWidth = 2;
  ctx.strokeStyle = cyan;
  ctx.strokeRect(35, 25, pillW, pillH);

  // Cyan active pip
  ctx.fillStyle = cyan;
  ctx.fillRect(45, 33, 6, pillH - 16);

  ctx.font = isUrduText(pageName) 
    ? '800 24px "Noto Sans Arabic", "Noto Nastaliq Urdu", sans-serif'
    : '900 26px "Montserrat", "Impact", sans-serif';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.fillText(pageName.toUpperCase(), 62, 25 + pillH / 2);

  // Top-right Red LIVE HD Badge
  const liveW = 110;
  const liveH = 46;
  const liveX = width - liveW - 35;
  const liveY = 28;
  ctx.fillStyle = '#e50914';
  ctx.fillRect(liveX, liveY, liveW, liveH);
  ctx.lineWidth = 2;
  ctx.strokeStyle = '#ffffff';
  ctx.strokeRect(liveX, liveY, liveW, liveH);

  ctx.font = '800 20px "Inter", sans-serif';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('🔴 LIVE HD', liveX + liveW / 2, liveY + liveH / 2);

  // Bottom photo category tag
  ctx.font = isUrduText(categoryTag)
    ? '800 24px "Noto Sans Arabic", "Noto Nastaliq Urdu", sans-serif'
    : '800 22px "Inter", sans-serif';
  const tagW = ctx.measureText(categoryTag).width + 36;
  const tagH = 44;
  const tagX = isUrdu ? width - tagW - 35 : 35;
  const tagY = splitY - tagH - 16;

  ctx.fillStyle = 'rgba(0, 240, 255, 0.95)';
  ctx.fillRect(tagX, tagY, tagW, tagH);
  ctx.fillStyle = '#050a12';
  ctx.textAlign = 'center';
  ctx.fillText(categoryTag, tagX + tagW / 2, tagY + tagH / 2);

  // 3. Neon Divider Beam
  ctx.fillStyle = cyan;
  ctx.fillRect(0, splitY - 2, width, 5);
  // Neon glow seam
  const neonSeam = ctx.createLinearGradient(0, splitY + 3, 0, splitY + 22);
  neonSeam.addColorStop(0, 'rgba(0, 240, 255, 0.45)');
  neonSeam.addColorStop(1, 'rgba(0, 240, 255, 0)');
  ctx.fillStyle = neonSeam;
  ctx.fillRect(0, splitY + 3, width, 19);

  // 4. Lower Half: Dark Obsidian Studio Deck
  const lowerGrad = ctx.createLinearGradient(0, splitY, 0, height);
  lowerGrad.addColorStop(0, '#0c1322');
  lowerGrad.addColorStop(1, '#05070d');
  ctx.fillStyle = lowerGrad;
  ctx.fillRect(0, splitY + 3, width, height - splitY - 3);

  // Floating Glassmorphism Container for Headline
  const boxMargin = 30;
  const boxTop = splitY + 25;
  const boxW = width - (boxMargin * 2);
  const boxH = height - boxTop - 78;

  ctx.fillStyle = 'rgba(12, 19, 34, 0.88)';
  ctx.fillRect(boxMargin, boxTop, boxW, boxH);
  ctx.lineWidth = 1.5;
  ctx.strokeStyle = 'rgba(0, 240, 255, 0.35)';
  ctx.strokeRect(boxMargin, boxTop, boxW, boxH);

  // Accent side stripe on card
  ctx.fillStyle = cyan;
  if (isUrdu) {
    ctx.fillRect(boxMargin + boxW - 8, boxTop + 14, 8, boxH - 28);
  } else {
    ctx.fillRect(boxMargin, boxTop + 14, 8, boxH - 28);
  }

  // 5. Headline
  const headlineFont = isUrdu
    ? `800 ${fontSize}px "Noto Sans Arabic", "Noto Nastaliq Urdu", 'Segoe UI', sans-serif`
    : `900 ${fontSize}px "Impact", "Montserrat", sans-serif`;
  ctx.font = headlineFont;

  const maxTextW = boxW - 70;
  const headlineLines = wrapText(ctx, title, maxTextW).slice(0, 3);
  const lineH = Math.floor(fontSize * 1.5);

  const fontSummary = isUrdu
    ? '700 24px "Noto Sans Arabic", "Noto Nastaliq Urdu", sans-serif'
    : '600 22px "Inter", sans-serif';
  ctx.font = fontSummary;
  const summaryLines = summary ? wrapText(ctx, summary, maxTextW).slice(0, 2) : [];
  const summaryLineH = 34;

  const totalTextH = (headlineLines.length * lineH) + (summaryLines.length > 0 ? (summaryLines.length * summaryLineH + 20) : 0);
  let curY = boxTop + Math.max(24, Math.floor((boxH - totalTextH) / 2)) + Math.floor(fontSize * 0.75);

  ctx.font = headlineFont;
  const align = currentStudioState.textAlign === 'auto' ? (isUrdu ? 'right' : 'left') : currentStudioState.textAlign;
  ctx.textAlign = align;
  let textX = boxMargin + 35;
  if (align === 'center') textX = width / 2;
  if (align === 'right') textX = boxMargin + boxW - 35;

  const hlColor = currentStudioState.headlineColor || '#ffffff';

  headlineLines.forEach(line => {
    // Sharp drop shadow
    ctx.fillStyle = 'rgba(0, 0, 0, 0.9)';
    ctx.fillText(line, textX + 3, curY + 3);
    ctx.fillStyle = hlColor;
    ctx.fillText(line, textX, curY);
    curY += lineH;
  });

  if (summaryLines.length > 0) {
    curY += 10;
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.25)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(boxMargin + 30, curY - 14);
    ctx.lineTo(boxMargin + boxW - 30, curY - 14);
    ctx.stroke();

    ctx.font = fontSummary;
    summaryLines.forEach(sLine => {
      ctx.fillStyle = 'rgba(215, 230, 250, 0.92)';
      ctx.fillText(sLine, textX, curY);
      curY += summaryLineH;
    });
  }

  // 6. Modern Cyber Footer
  const footerY = height - 58;
  ctx.fillStyle = '#04060b';
  ctx.fillRect(0, footerY, width, 58);
  ctx.fillStyle = cyan;
  ctx.fillRect(0, footerY, width, 2);

  ctx.font = isUrdu ? '700 22px "Noto Sans Arabic", sans-serif' : '700 22px "Inter", sans-serif';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  const srcLabel = isUrdu ? `⚡ ذرائع: ${source}` : `⚡ SOURCE: ${source}`;
  ctx.fillText(srcLabel, 35, footerY + 30);

  ctx.font = '700 22px "Inter", sans-serif';
  ctx.fillStyle = cyan;
  ctx.textAlign = 'right';
  ctx.fillText(`Follow ${handle}`, width - 35, footerY + 30);
}

// ========================================================
// 5. ROYAL GOLD & VELVET BULLETIN (Prime-time Luxury)
// ========================================================
function renderRoyalGoldSplitLayout(theme, width, height, pageName, categoryTag, title, summary, source, handle, fontSize, isUrdu) {
  const splitY = Math.floor(height * 0.53);
  const gold = '#ffd700';
  const goldLight = '#fff2a3';

  // 1. Background
  ctx.fillStyle = '#120003';
  ctx.fillRect(0, 0, width, height);

  // 2. Photo (Fit in top 53% - perfect wide framing)
  drawFittedPhoto(ctx, currentStudioState.loadedImg, 0, 0, width, splitY);

  if (currentStudioState.overlayDarkness > 0) {
    ctx.fillStyle = `rgba(0, 0, 0, ${currentStudioState.overlayDarkness / 100})`;
    ctx.fillRect(0, 0, width, splitY);
  }

  // Luxury Gold Border around photo
  ctx.lineWidth = 3;
  ctx.strokeStyle = gold;
  ctx.strokeRect(4, 4, width - 8, splitY - 4);

  // Top-Left Gold Crest Box
  const crestW = Math.max(220, ctx.measureText(pageName).width + 60);
  const crestH = 60;
  ctx.fillStyle = '#ffd700';
  ctx.fillRect(25, 20, crestW, crestH);
  ctx.fillStyle = '#2c0006';
  ctx.fillRect(28, 23, crestW - 6, crestH - 6);

  ctx.font = isUrduText(pageName) 
    ? '800 26px "Noto Sans Arabic", "Noto Nastaliq Urdu", sans-serif'
    : '900 28px "Montserrat", "Impact", sans-serif';
  ctx.fillStyle = goldLight;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(pageName.toUpperCase(), 25 + crestW / 2, 20 + crestH / 2);

  // Top-Right Deep Red & Gold LIVE Badge
  const liveW = 105;
  const liveH = 44;
  const liveX = width - liveW - 25;
  const liveY = 22;
  ctx.fillStyle = '#9e0018';
  ctx.fillRect(liveX, liveY, liveW, liveH);
  ctx.lineWidth = 2.5;
  ctx.strokeStyle = gold;
  ctx.strokeRect(liveX, liveY, liveW, liveH);

  ctx.font = '800 20px "Inter", sans-serif';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'center';
  ctx.fillText('🔴 LIVE', liveX + liveW / 2, liveY + liveH / 2);

  // 3. Dual Gold Ribbon Divider with Center Jewel
  ctx.fillStyle = '#ffd700';
  ctx.fillRect(0, splitY, width, 6);
  ctx.fillStyle = '#997a00';
  ctx.fillRect(0, splitY + 6, width, 3);

  // Center Diamond Jewel
  const midX = width / 2;
  ctx.save();
  ctx.translate(midX, splitY + 4);
  ctx.rotate(Math.PI / 4);
  ctx.fillStyle = '#ffd700';
  ctx.fillRect(-12, -12, 24, 24);
  ctx.fillStyle = '#42000c';
  ctx.fillRect(-8, -8, 16, 16);
  ctx.restore();

  // 4. Lower Half: Royal Burgundy Velvet Gradient
  const velvetGrad = ctx.createLinearGradient(0, splitY + 9, 0, height);
  velvetGrad.addColorStop(0, '#42000c');
  velvetGrad.addColorStop(0.4, '#2d0007');
  velvetGrad.addColorStop(1, '#160003');
  ctx.fillStyle = velvetGrad;
  ctx.fillRect(0, splitY + 9, width, height - splitY - 9);

  // Category Badge in Pure Gold
  ctx.font = isUrduText(categoryTag)
    ? '800 26px "Noto Sans Arabic", "Noto Nastaliq Urdu", sans-serif'
    : '800 24px "Montserrat", "Impact", sans-serif';
  const catTagW = ctx.measureText(categoryTag).width + 42;
  const catTagH = 46;
  const catTagX = isUrdu ? width - catTagW - 40 : 40;
  const catTagY = splitY + 28;

  ctx.fillStyle = gold;
  ctx.fillRect(catTagX, catTagY, catTagW, catTagH);
  ctx.fillStyle = '#1e0004';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(categoryTag, catTagX + catTagW / 2, catTagY + catTagH / 2);

  // 5. Headline Text (Radiant Liquid Gold with 3D Depth)
  const headlineFont = isUrdu
    ? `800 ${fontSize}px "Noto Sans Arabic", "Noto Nastaliq Urdu", sans-serif`
    : `900 ${fontSize}px "Impact", "Montserrat", sans-serif`;
  ctx.font = headlineFont;

  const maxTextW = width - 100;
  const headlineLines = wrapText(ctx, title, maxTextW).slice(0, 3);
  const lineH = Math.floor(fontSize * 1.55);

  const fontSummary = isUrdu
    ? '700 25px "Noto Sans Arabic", "Noto Nastaliq Urdu", sans-serif'
    : '600 23px "Inter", sans-serif';
  ctx.font = fontSummary;
  const summaryLines = summary ? wrapText(ctx, summary, maxTextW).slice(0, 2) : [];
  const summaryLineH = 36;

  const totalTextH = (headlineLines.length * lineH) + (summaryLines.length > 0 ? (summaryLines.length * summaryLineH + 20) : 0);
  const availableBottomH = height - (catTagY + catTagH) - 80;
  let curY = (catTagY + catTagH) + Math.max(20, Math.floor((availableBottomH - totalTextH) / 2)) + Math.floor(fontSize * 0.75);

  ctx.font = headlineFont;
  const align = currentStudioState.textAlign === 'auto' ? (isUrdu ? 'right' : 'left') : currentStudioState.textAlign;
  ctx.textAlign = align;
  let textX = 50;
  if (align === 'center') textX = width / 2;
  if (align === 'right') textX = width - 50;

  const hlColor = currentStudioState.headlineColor || gold;

  headlineLines.forEach(line => {
    // Deep 3D drop shadow
    ctx.fillStyle = 'rgba(0, 0, 0, 0.95)';
    ctx.fillText(line, textX + 3, curY + 3);
    ctx.fillStyle = hlColor;
    ctx.fillText(line, textX, curY);
    curY += lineH;
  });

  if (summaryLines.length > 0) {
    curY += 10;
    ctx.strokeStyle = 'rgba(255, 215, 0, 0.35)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(50, curY - 14);
    ctx.lineTo(width - 50, curY - 14);
    ctx.stroke();

    ctx.font = fontSummary;
    summaryLines.forEach(sLine => {
      ctx.fillStyle = 'rgba(255, 245, 230, 0.95)';
      ctx.fillText(sLine, textX, curY);
      curY += summaryLineH;
    });
  }

  // 6. Royal Gold Footer
  const footerH = 65;
  const footerY = height - footerH;
  ctx.fillStyle = '#140003';
  ctx.fillRect(0, footerY, width, footerH);
  ctx.fillStyle = gold;
  ctx.fillRect(0, footerY, width, 3);

  // Source Crest Pill
  ctx.font = isUrdu ? '700 22px "Noto Sans Arabic", sans-serif' : '700 22px "Inter", sans-serif';
  ctx.fillStyle = goldLight;
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  const srcLabel = isUrdu ? `👑 ذرائع: ${source}` : `👑 SOURCE: ${source}`;
  ctx.fillText(srcLabel, 35, footerY + footerH / 2);

  ctx.font = '700 24px "Inter", sans-serif';
  ctx.fillStyle = gold;
  ctx.textAlign = 'right';
  ctx.fillText(`Follow ${handle}`, width - 35, footerY + footerH / 2);
}

// ========================================================
// 6. GLOBAL SPOTLIGHT / VOX CLEAN (High-Prestige Editorial)
// ========================================================
function renderVoxSpotlightLayout(theme, width, height, pageName, categoryTag, title, summary, source, handle, fontSize, isUrdu) {
  const splitY = Math.floor(height * 0.54);
  const limeAccent = '#ccff00';

  // 1. Background
  ctx.fillStyle = '#0d0f14';
  ctx.fillRect(0, 0, width, height);

  // 2. Photo (Fit cleanly in top 54%)
  drawFittedPhoto(ctx, currentStudioState.loadedImg, 0, 0, width, splitY);

  if (currentStudioState.overlayDarkness > 0) {
    ctx.fillStyle = `rgba(0, 0, 0, ${currentStudioState.overlayDarkness / 100})`;
    ctx.fillRect(0, 0, width, splitY);
  }

  // Bottom vignette on photo
  const photoBottomGrad = ctx.createLinearGradient(0, splitY - 120, 0, splitY);
  photoBottomGrad.addColorStop(0, 'rgba(13, 15, 20, 0)');
  photoBottomGrad.addColorStop(1, 'rgba(13, 15, 20, 0.95)');
  ctx.fillStyle = photoBottomGrad;
  ctx.fillRect(0, splitY - 120, width, 120);

  // Brand Name Top Bar
  const topH = 70;
  ctx.fillStyle = 'rgba(13, 15, 20, 0.85)';
  ctx.fillRect(0, 0, width, topH);
  ctx.fillStyle = limeAccent;
  ctx.fillRect(0, topH - 3, width, 3);

  ctx.font = isUrduText(pageName) 
    ? '800 30px "Noto Sans Arabic", sans-serif'
    : '900 32px "Montserrat", "Impact", sans-serif';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.fillText(pageName.toUpperCase(), 35, topH / 2);

  // Angled Exclusive Ribbon
  const ribW = 200;
  const ribH = 42;
  const ribX = width - ribW - 30;
  const ribY = (topH - ribH) / 2;
  ctx.fillStyle = limeAccent;
  ctx.fillRect(ribX, ribY, ribW, ribH);
  ctx.font = '800 20px "Inter", sans-serif';
  ctx.fillStyle = '#000000';
  ctx.textAlign = 'center';
  ctx.fillText('✦ SPECIAL REPORT', ribX + ribW / 2, ribY + ribH / 2);

  // 3. Category Tag Ribbon resting on photo baseline
  ctx.font = isUrduText(categoryTag)
    ? '800 26px "Noto Sans Arabic", sans-serif'
    : '900 24px "Inter", sans-serif';
  const tagW = ctx.measureText(categoryTag).width + 36;
  const tagH = 46;
  const tagX = isUrdu ? width - tagW - 40 : 40;
  const tagY = splitY - tagH;

  ctx.fillStyle = '#e50914';
  ctx.fillRect(tagX, tagY, tagW, tagH);
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'center';
  ctx.fillText(categoryTag, tagX + tagW / 2, tagY + tagH / 2);

  // 4. Lower Half: Matte Editorial Charcoal
  ctx.fillStyle = '#0f1219';
  ctx.fillRect(0, splitY, width, height - splitY);

  // Asymmetric Thick Accent Pillar
  ctx.fillStyle = limeAccent;
  if (isUrdu) {
    ctx.fillRect(width - 24, splitY + 20, 8, height - splitY - 95);
  } else {
    ctx.fillRect(16, splitY + 20, 8, height - splitY - 95);
  }

  // 5. Headline
  const headlineFont = isUrdu
    ? `800 ${fontSize}px "Noto Sans Arabic", "Noto Nastaliq Urdu", sans-serif`
    : `900 ${fontSize}px "Impact", "Montserrat", sans-serif`;
  ctx.font = headlineFont;

  const maxTextW = width - 110;
  const headlineLines = wrapText(ctx, title, maxTextW).slice(0, 3);
  const lineH = Math.floor(fontSize * 1.55);

  const fontSummary = isUrdu
    ? '700 25px "Noto Sans Arabic", sans-serif'
    : '600 23px "Inter", sans-serif';
  ctx.font = fontSummary;
  const summaryLines = summary ? wrapText(ctx, summary, maxTextW).slice(0, 2) : [];
  const summaryLineH = 36;

  const totalTextH = (headlineLines.length * lineH) + (summaryLines.length > 0 ? (summaryLines.length * summaryLineH + 20) : 0);
  const availableBottomH = height - splitY - 80;
  let curY = splitY + Math.max(25, Math.floor((availableBottomH - totalTextH) / 2)) + Math.floor(fontSize * 0.75);

  ctx.font = headlineFont;
  const align = currentStudioState.textAlign === 'auto' ? (isUrdu ? 'right' : 'left') : currentStudioState.textAlign;
  ctx.textAlign = align;
  let textX = 45;
  if (align === 'center') textX = width / 2;
  if (align === 'right') textX = width - 45;

  const hlColor = currentStudioState.headlineColor || '#ffffff';

  headlineLines.forEach(line => {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.9)';
    ctx.fillText(line, textX + 3, curY + 3);
    ctx.fillStyle = hlColor;
    ctx.fillText(line, textX, curY);
    curY += lineH;
  });

  if (summaryLines.length > 0) {
    curY += 12;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.18)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(40, curY - 14);
    ctx.lineTo(width - 40, curY - 14);
    ctx.stroke();

    ctx.font = fontSummary;
    summaryLines.forEach(sLine => {
      ctx.fillStyle = 'rgba(200, 215, 235, 0.92)';
      ctx.fillText(sLine, textX, curY);
      curY += summaryLineH;
    });
  }

  // 6. Minimalist Footer
  const footerH = 65;
  const footerY = height - footerH;
  ctx.fillStyle = '#080a0f';
  ctx.fillRect(0, footerY, width, footerH);

  ctx.font = isUrdu ? '700 22px "Noto Sans Arabic", sans-serif' : '700 22px "Inter", sans-serif';
  ctx.fillStyle = '#94a3b8';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  const srcLabel = isUrdu ? `ذرائع: ${source}` : `SOURCE: ${source}`;
  ctx.fillText(srcLabel, 35, footerY + footerH / 2);

  ctx.font = '700 24px "Inter", sans-serif';
  ctx.fillStyle = limeAccent;
  ctx.textAlign = 'right';
  ctx.fillText(`Follow ${handle}`, width - 35, footerY + footerH / 2);
}

// ========================================================
// 7. TV LIVE TICKER 24/7 (Real Television Simulation)
// ========================================================
function renderTickerTVLayout(theme, width, height, pageName, categoryTag, title, summary, source, handle, fontSize, isUrdu) {
  const photoH = Math.floor(height * 0.58);
  const tickerH = 56;
  const tickerY = photoH;

  // 1. Background
  ctx.fillStyle = '#070c16';
  ctx.fillRect(0, 0, width, height);

  // 2. Photo (Fit cleanly in top 58%)
  drawFittedPhoto(ctx, currentStudioState.loadedImg, 0, 0, width, photoH);

  if (currentStudioState.overlayDarkness > 0) {
    ctx.fillStyle = `rgba(0, 0, 0, ${currentStudioState.overlayDarkness / 100})`;
    ctx.fillRect(0, 0, width, photoH);
  }

  // Top TV Broadcast Bar
  const topH = 75;
  ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
  ctx.fillRect(0, 0, width, topH);
  ctx.fillStyle = '#ff1e38';
  ctx.fillRect(0, topH - 4, width, 4);

  ctx.font = isUrduText(pageName) 
    ? '800 32px "Noto Sans Arabic", sans-serif'
    : '900 36px "Impact", "Montserrat", sans-serif';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.fillText(pageName.toUpperCase(), 35, topH / 2);

  // HD + LIVE Pill (Top-Right)
  const liveW = 125;
  const liveH = 46;
  const liveX = width - liveW - 30;
  const liveY = (topH - liveH) / 2;
  ctx.fillStyle = '#cc0015';
  ctx.fillRect(liveX, liveY, liveW, liveH);
  ctx.lineWidth = 2;
  ctx.strokeStyle = '#ffffff';
  ctx.strokeRect(liveX, liveY, liveW, liveH);

  ctx.font = '800 20px "Inter", sans-serif';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'center';
  ctx.fillText('🔴 LIVE HD', liveX + liveW / 2, liveY + liveH / 2);

  // 3. Authentically Styled Breaking News Ticker
  ctx.fillStyle = '#b30012';
  ctx.fillRect(0, tickerY, width, tickerH);

  // Yellow warning stripe at bottom of ticker
  ctx.fillStyle = '#ffd700';
  ctx.fillRect(0, tickerY + tickerH - 4, width, 4);

  // Ticker Left Tab
  const tabW = 240;
  ctx.fillStyle = '#ffd700';
  ctx.fillRect(0, tickerY, tabW, tickerH - 4);
  ctx.font = isUrduText(categoryTag) 
    ? '900 24px "Noto Sans Arabic", sans-serif'
    : '900 22px "Impact", "Montserrat", sans-serif';
  ctx.fillStyle = '#000000';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(`▶ BREAKING NEWS`, tabW / 2, tickerY + (tickerH - 4) / 2);

  // Ticker Content
  ctx.save();
  ctx.beginPath();
  ctx.rect(tabW + 10, tickerY, width - tabW - 20, tickerH - 4);
  ctx.clip();
  ctx.font = isUrdu ? '700 24px "Noto Sans Arabic", sans-serif' : '700 22px "Inter", sans-serif';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'left';
  ctx.fillText(`● ${title}  ●  تازہ ترین بریکنگ نیوز  ●  ${source}`, tabW + 20, tickerY + (tickerH - 4) / 2);
  ctx.restore();

  // 4. Lower Deck: Newsroom Anchor Plate
  const deskY = tickerY + tickerH;
  const deskH = height - deskY;
  const deskGrad = ctx.createLinearGradient(0, deskY, 0, height);
  deskGrad.addColorStop(0, '#0c1527');
  deskGrad.addColorStop(1, '#050a14');
  ctx.fillStyle = deskGrad;
  ctx.fillRect(0, deskY, width, deskH);

  // Left red anchor accent
  ctx.fillStyle = '#ff1e38';
  ctx.fillRect(0, deskY, 8, deskH - 60);

  // 5. Headline Text
  const headlineFont = isUrdu
    ? `800 ${fontSize}px "Noto Sans Arabic", "Noto Nastaliq Urdu", sans-serif`
    : `900 ${fontSize}px "Impact", "Montserrat", sans-serif`;
  ctx.font = headlineFont;

  const maxTextW = width - 90;
  const headlineLines = wrapText(ctx, title, maxTextW).slice(0, 3);
  const lineH = Math.floor(fontSize * 1.55);

  const fontSummary = isUrdu
    ? '700 24px "Noto Sans Arabic", sans-serif'
    : '600 22px "Inter", sans-serif';
  ctx.font = fontSummary;
  const summaryLines = summary ? wrapText(ctx, summary, maxTextW).slice(0, 2) : [];
  const summaryLineH = 34;

  const totalTextH = (headlineLines.length * lineH) + (summaryLines.length > 0 ? (summaryLines.length * summaryLineH + 16) : 0);
  const availableBottomH = deskH - 65;
  let curY = deskY + Math.max(20, Math.floor((availableBottomH - totalTextH) / 2)) + Math.floor(fontSize * 0.75);

  ctx.font = headlineFont;
  const align = currentStudioState.textAlign === 'auto' ? (isUrdu ? 'right' : 'left') : currentStudioState.textAlign;
  ctx.textAlign = align;
  let textX = 40;
  if (align === 'center') textX = width / 2;
  if (align === 'right') textX = width - 40;

  const hlColor = currentStudioState.headlineColor || '#ffffff';

  headlineLines.forEach(line => {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.9)';
    ctx.fillText(line, textX + 3, curY + 3);
    ctx.fillStyle = hlColor;
    ctx.fillText(line, textX, curY);
    curY += lineH;
  });

  if (summaryLines.length > 0) {
    curY += 10;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(35, curY - 12);
    ctx.lineTo(width - 35, curY - 12);
    ctx.stroke();

    ctx.font = fontSummary;
    summaryLines.forEach(sLine => {
      ctx.fillStyle = 'rgba(215, 230, 250, 0.92)';
      ctx.fillText(sLine, textX, curY);
      curY += summaryLineH;
    });
  }

  // 6. Broadcast Desk Footer
  const footerH = 58;
  const footerY = height - footerH;
  ctx.fillStyle = '#04070d';
  ctx.fillRect(0, footerY, width, footerH);
  ctx.fillStyle = '#ff1e38';
  ctx.fillRect(0, footerY, width, 2);

  ctx.font = isUrdu ? '700 22px "Noto Sans Arabic", sans-serif' : '700 22px "Inter", sans-serif';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  const srcLabel = isUrdu ? `📡 ذرائع: ${source}` : `📡 SOURCE: ${source}`;
  ctx.fillText(srcLabel, 35, footerY + footerH / 2);

  ctx.font = '700 22px "Inter", sans-serif';
  ctx.fillStyle = '#ffd700';
  ctx.textAlign = 'right';
  ctx.fillText(`Follow ${handle}`, width - 35, footerY + footerH / 2);
}

// ========================================================
// 8. CINEMATIC LETTERBOX NOIR (Anamorphic Cinema Style)
// ========================================================
function renderCinematicLetterboxLayout(theme, width, height, pageName, categoryTag, title, summary, source, handle, fontSize, isUrdu) {
  const topBarH = Math.floor(height * 0.12);
  const botBarH = Math.floor(height * 0.24);
  const midH = height - topBarH - botBarH;
  const redAccent = '#ff1e38';

  // 1. Solid Matte Black Background
  ctx.fillStyle = '#000000';
  ctx.fillRect(0, 0, width, height);

  // 2. Center Panoramic Photo (Wide 16:9 Cinema Viewport - NO head crop)
  drawFittedPhoto(ctx, currentStudioState.loadedImg, 0, topBarH, width, midH);

  if (currentStudioState.overlayDarkness > 0) {
    ctx.fillStyle = `rgba(0, 0, 0, ${currentStudioState.overlayDarkness / 100})`;
    ctx.fillRect(0, topBarH, width, midH);
  }

  // Cinema Vignette on photo
  const topVig = ctx.createLinearGradient(0, topBarH, 0, topBarH + 60);
  topVig.addColorStop(0, 'rgba(0, 0, 0, 0.7)');
  topVig.addColorStop(1, 'rgba(0, 0, 0, 0)');
  ctx.fillStyle = topVig;
  ctx.fillRect(0, topBarH, width, 60);

  const botVig = ctx.createLinearGradient(0, topBarH + midH - 60, 0, topBarH + midH);
  botVig.addColorStop(0, 'rgba(0, 0, 0, 0)');
  botVig.addColorStop(1, 'rgba(0, 0, 0, 0.7)');
  ctx.fillStyle = botVig;
  ctx.fillRect(0, topBarH + midH - 60, width, 60);

  // 3. Top Letterbox Bar Content
  ctx.fillStyle = '#000000';
  ctx.fillRect(0, 0, width, topBarH);

  ctx.font = isUrduText(pageName) 
    ? '800 32px "Noto Sans Arabic", sans-serif'
    : '900 36px "Montserrat", "Impact", sans-serif';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.fillText(pageName.toUpperCase(), 40, topBarH / 2);

  // Cinema Exclusive Tag (Top-Right)
  const excW = 210;
  const excH = 46;
  const excX = width - excW - 35;
  const excY = (topBarH - excH) / 2;
  ctx.fillStyle = redAccent;
  ctx.fillRect(excX, excY, excW, excH);
  ctx.font = '800 20px "Impact", "Montserrat", sans-serif';
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'center';
  ctx.fillText('✦ CINEMA SPECIAL', excX + excW / 2, excY + excH / 2);

  // 4. Glowing Red Razor Line above Bottom Letterbox
  const lineY = topBarH + midH;
  ctx.fillStyle = redAccent;
  ctx.fillRect(0, lineY - 3, width, 4);

  // 5. Bottom Letterbox Bar Content
  ctx.fillStyle = '#000000';
  ctx.fillRect(0, lineY + 1, width, botBarH);

  // Headline in Bold Cinema Style
  const headlineFont = isUrdu
    ? `800 ${Math.min(fontSize, 56)}px "Noto Sans Arabic", "Noto Nastaliq Urdu", sans-serif`
    : `900 ${Math.min(fontSize, 58)}px "Impact", "Montserrat", sans-serif`;
  ctx.font = headlineFont;

  const maxTextW = width - 100;
  const headlineLines = wrapText(ctx, title, maxTextW).slice(0, 2);
  const lineH = Math.floor(Math.min(fontSize, 56) * 1.45);

  const totalTextH = headlineLines.length * lineH + 34;
  let curY = lineY + Math.max(20, Math.floor((botBarH - totalTextH) / 2)) + Math.floor(Math.min(fontSize, 56) * 0.75);

  ctx.font = headlineFont;
  const align = currentStudioState.textAlign === 'auto' ? 'center' : currentStudioState.textAlign;
  ctx.textAlign = align;
  let textX = width / 2;
  if (align === 'right') textX = width - 50;
  if (align === 'left') textX = 50;

  const hlColor = currentStudioState.headlineColor || '#ffffff';

  headlineLines.forEach(line => {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.9)';
    ctx.fillText(line, textX + 3, curY + 3);
    ctx.fillStyle = hlColor;
    ctx.fillText(line, textX, curY);
    curY += lineH;
  });

  // Source & Handle in Subtitle Style
  ctx.font = isUrdu ? '600 22px "Noto Sans Arabic", sans-serif' : '600 22px "Inter", sans-serif';
  ctx.fillStyle = 'rgba(200, 205, 215, 0.85)';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'alphabetic';
  ctx.fillText(`${source}   |   ${categoryTag}   |   ${handle}`, width / 2, height - 20);
}

function downloadCurrentCanvas() {
  if (!canvas) return;
  const link = document.createElement('a');
  const timestamp = new Date().toISOString().replace(/[-:T.]/g, '').slice(0, 14);
  link.download = `ViralNews_${currentStudioState.theme}_${timestamp}.png`;
  link.href = canvas.toDataURL('image/png', 0.96);
  link.click();
  showToast('Graphic Downloaded', 'High-res news card PNG saved to your downloads folder!');
}
