// Frontend JavaScript for AI Pitch Deck Generator
let currentSlides = [];
let currentSlideIndex = 0;
let currentDeckTitle = '';
let currentDeckId = null;
let pitchProgress = { generated: false, refined: false, exported: false };
let selectedDeckTheme = localStorage.getItem('deckPresentationTheme') || 'professional';
let pendingDeckTheme = selectedDeckTheme;
let practiceIndex = 0;
let practiceSeconds = 0;
let practiceTimer = null;

const SAMPLES = [
  { companyName: 'MedPulse AI', industry: 'Healthcare & HealthTech', tagline: 'Predictive Remote Diagnostic Triage Powered by Clinical Machine Learning', problemStatement: 'Patients may face delays in getting the right care because symptoms can be difficult to assess quickly and healthcare teams have limited time.', solutionDescription: 'An AI-assisted health support platform that organizes symptom information and helps users identify when professional medical attention may be needed.' },
  { companyName: 'EcoTrack Logistics', industry: 'Supply Chain & CleanTech', tagline: 'Zero-Emission Autonomous Route Optimization for Commercial Freight Fleets', problemStatement: 'Delivery teams often spend extra time and fuel because routes are not always planned efficiently and vehicles may travel with unused capacity.', solutionDescription: 'An AI route-planning system that suggests efficient delivery routes, helps coordinate charging stops, and reduces unnecessary travel.' },
  { companyName: 'CodeCraft Mentor', industry: 'EdTech & Developer Tools', tagline: 'Interactive AI Pair-Programmer & Curriculum Engine for Computer Science Students', problemStatement: 'Computer science students can find programming and algorithm concepts difficult when they do not receive enough personalized guidance or clear explanations.', solutionDescription: 'An adaptive AI tutor that explains code step by step, visualizes programming concepts, and creates practice questions based on the learner’s needs.' }
];

function loadSample(idx) {
  const sample = SAMPLES[idx];
  Object.entries(sample).forEach(([key, value]) => { const el = document.getElementById(key); if (el) el.value = value; });
  showToast('Sample idea loaded. Ready to generate!', 'success');
}

function setGeneratingState(active) {
  const btn = document.getElementById('btn-generate');
  btn.disabled = active;
  if (active) {
    btn.innerHTML = '<span class="spinner"></span> AI is building your deck...';
    document.getElementById('slide-stage').classList.add('is-generating');
  } else {
    btn.innerHTML = '✨ Generate AI Pitch Deck';
    document.getElementById('slide-stage').classList.remove('is-generating');
  }
}

document.getElementById('pitch-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  setGeneratingState(true);
  const payload = {
    companyName: document.getElementById('companyName').value,
    industry: document.getElementById('industry').value,
    tagline: document.getElementById('tagline').value,
    problemStatement: document.getElementById('problemStatement').value,
    solutionDescription: document.getElementById('solutionDescription').value,
    targetAudience: document.getElementById('targetAudience').value,
    targetMarket: document.getElementById('targetMarket').value,
    knownUserBase: document.getElementById('knownUserBase').value,
    monthlyPrice: document.getElementById('monthlyPrice').value,
    monthlyCosts: document.getElementById('monthlyCosts').value,
    customerVariableCost: document.getElementById('customerVariableCost').value,
    monthlyMarketing: document.getElementById('monthlyMarketing').value,
    newCustomersMonthly: document.getElementById('newCustomersMonthly').value,
    marketCustomers: document.getElementById('marketCustomers').value,
    marketPenetration: document.getElementById('marketPenetration').value,
    theme: selectedDeckTheme
  };
  try {
    const res = await fetch('/api/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    const data = await res.json();
    if (!res.ok || !data.slides) throw new Error(data.error || 'Generation failed');
    loadDeckIntoWorkspace(data);
    showToast('🎉 Your AI pitch deck is ready!', 'success');
    loadRecentDecks();
  } catch (err) {
    alert('Error generating pitch deck: ' + err.message);
  } finally {
    setGeneratingState(false);
  }
});

function loadDeckIntoWorkspace(data) {
  currentSlides = data.slides || [];
  currentDeckTitle = data.title || 'Pitch Deck';
  currentDeckId = data.deck_id || data.id || null;
  if (['professional', 'startup', 'dark'].includes(data.theme)) {
    selectedDeckTheme = data.theme;
    pendingDeckTheme = data.theme;
    localStorage.setItem('deckPresentationTheme', selectedDeckTheme);
  }
  currentSlideIndex = 0;
  document.getElementById('empty-state').style.display = currentSlides.length ? 'none' : 'flex';
  document.getElementById('active-slide-view').style.display = currentSlides.length ? 'flex' : 'none';
  document.getElementById('carousel-controls').style.display = currentSlides.length ? 'flex' : 'none';
  document.getElementById('thumbnails-strip').style.display = currentSlides.length ? 'flex' : 'none';
  document.getElementById('slide-progress-wrap').style.display = currentSlides.length ? 'block' : 'none';
  document.getElementById('btn-theme-deck').disabled = !currentSlides.length;
  document.getElementById('btn-export-menu').disabled = !currentSlides.length;
  document.getElementById('btn-improve').disabled = !currentSlides.length;
  document.getElementById('btn-practice').disabled = !currentSlides.length;
  document.getElementById('btn-edit-slide').disabled = !currentSlides.length;
  document.getElementById('btn-rewrite').disabled = !currentSlides.length;
  pitchProgress.generated = currentSlides.length > 0;
  pitchProgress.refined = false;
  updatePitchProgress();
  document.getElementById('btn-fullscreen').disabled = !currentSlides.length;
  document.getElementById('deck-title-display').textContent = currentDeckTitle + ' Pitch Deck';
  document.getElementById('deck-slide-count').textContent = currentSlides.length + ' Slides Generated';
  renderActiveSlide();
  renderThumbnails();
}

function renderActiveSlide() {
  if (!currentSlides.length) return;
  const slide = currentSlides[currentSlideIndex];
  document.getElementById('slide-category').textContent = (slide.category || 'OVERVIEW').toUpperCase();
  document.getElementById('slide-title').textContent = slide.title || '';
  document.getElementById('slide-subtitle').textContent = slide.subtitle || '';
  document.getElementById('slide-speaker-notes').textContent = slide.speaker_notes || 'None';
  document.getElementById('slide-indicator').textContent = `Slide ${currentSlideIndex + 1} / ${currentSlides.length}`;
  document.getElementById('progress-text').textContent = `${currentSlideIndex + 1} / ${currentSlides.length}`;
  document.getElementById('slide-progress').style.width = `${((currentSlideIndex + 1) / currentSlides.length) * 100}%`;

  const bulletsList = document.getElementById('slide-bullets');
  bulletsList.innerHTML = '';
  (slide.bullets || []).forEach(b => { const li = document.createElement('li'); li.textContent = b; bulletsList.appendChild(li); });

  const metricsBox = document.getElementById('slide-metrics');
  metricsBox.innerHTML = '';
  (slide.metrics || []).forEach(m => {
    const div = document.createElement('div'); div.className = 'metric-box';
    div.innerHTML = `<div class="metric-val">${escapeHtml(m.value)}</div><div class="metric-lbl">${escapeHtml(m.label)}</div>`;
    metricsBox.appendChild(div);
  });
  document.querySelectorAll('.thumb-card').forEach((el, idx) => el.classList.toggle('active', idx === currentSlideIndex));
}

function updatePitchProgress() {
  const steps = ['idea','generate','slides','refine','export'];
  const completed = { idea: true, generate: pitchProgress.generated, slides: pitchProgress.generated, refine: pitchProgress.refined, export: pitchProgress.exported };
  const active = pitchProgress.exported ? 'export' : pitchProgress.refined ? 'refine' : pitchProgress.generated ? 'slides' : 'idea';
  document.querySelectorAll('.pitch-step').forEach(step => { const key = step.dataset.step; step.classList.toggle('done', !!completed[key]); step.classList.toggle('active', key === active); });
  const doneCount = steps.filter(k => completed[k]).length;
  const percent = pitchProgress.exported ? 100 : pitchProgress.refined ? 80 : pitchProgress.generated ? 60 : 20;
  document.getElementById('pitch-percent').textContent = `${percent}%`;
  const labels = { idea: 'Idea captured — ready to build', slides: 'Deck generated — refine your pitch', refine: 'Pitch refined — ready to export', export: 'Pitch deck completed and exported' };
  document.getElementById('pitch-progress-label').textContent = labels[active];
}

function renderThumbnails() {
  const strip = document.getElementById('thumbnails-strip');
  strip.innerHTML = '';
  currentSlides.forEach((s, idx) => {
    const thumb = document.createElement('button');
    thumb.type = 'button';
    thumb.className = 'thumb-card' + (idx === currentSlideIndex ? ' active' : '');
    thumb.innerHTML = `<span class="thumb-number">${idx + 1}</span><span>${escapeHtml(s.title || 'Untitled')}</span>`;
    thumb.onclick = () => { currentSlideIndex = idx; renderActiveSlide(); };
    strip.appendChild(thumb);
  });
}

document.getElementById('btn-prev').addEventListener('click', () => { if (currentSlideIndex > 0) { currentSlideIndex--; renderActiveSlide(); } });
document.getElementById('btn-next').addEventListener('click', () => { if (currentSlideIndex < currentSlides.length - 1) { currentSlideIndex++; renderActiveSlide(); } });

// #3 Better preview: keyboard navigation + fullscreen preview
function toggleFullscreen() {
  const card = document.getElementById('preview-card');
  if (!document.fullscreenElement) card.requestFullscreen?.(); else document.exitFullscreen?.();
}
document.getElementById('btn-fullscreen').addEventListener('click', toggleFullscreen);
document.addEventListener('keydown', (e) => {
  if (!currentSlides.length || ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
  if (e.key === 'ArrowLeft' && currentSlideIndex > 0) { currentSlideIndex--; renderActiveSlide(); }
  if (e.key === 'ArrowRight' && currentSlideIndex < currentSlides.length - 1) { currentSlideIndex++; renderActiveSlide(); }
});

// #7 Export center
document.getElementById('btn-export-menu').addEventListener('click', () => openModal('export-modal'));
document.getElementById('btn-theme-deck').addEventListener('click', () => { pendingDeckTheme = selectedDeckTheme; updateThemeCards(); openModal('theme-modal'); });
function updateThemeCards() {
  document.querySelectorAll('[data-theme-choice]').forEach(card => card.classList.toggle('active', card.dataset.themeChoice === pendingDeckTheme));
  const labels = {professional:'Professional theme selected', startup:'Startup theme selected', dark:'Dark theme selected'};
  document.getElementById('theme-selected-label').textContent = labels[pendingDeckTheme] || labels.professional;
}
document.querySelectorAll('[data-theme-choice]').forEach(card => card.addEventListener('click', () => { pendingDeckTheme = card.dataset.themeChoice; updateThemeCards(); }));
document.getElementById('apply-theme').addEventListener('click', async () => {
  selectedDeckTheme = pendingDeckTheme;
  localStorage.setItem('deckPresentationTheme', selectedDeckTheme);
  applyDeckTheme();
  closeModal('theme-modal');
  if (currentDeckId) {
    try {
      const res = await fetch(`/api/decks/${currentDeckId}/theme`, { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify({theme: selectedDeckTheme}) });
      if (!res.ok) throw new Error('Theme could not be saved');
      showToast(`${selectedDeckTheme.charAt(0).toUpperCase()+selectedDeckTheme.slice(1)} theme applied and saved.`, 'success');
    } catch (err) {
      showToast('Theme applied for this session, but could not be saved to history.', 'warning');
    }
  } else {
    showToast(`${selectedDeckTheme.charAt(0).toUpperCase()+selectedDeckTheme.slice(1)} theme applied.`, 'success');
  }
});
function applyDeckTheme() {
  const stage = document.getElementById('slide-stage');
  if (stage) stage.dataset.presentationTheme = selectedDeckTheme;
  const label = document.getElementById('deck-theme-label');
  if (label) label.textContent = selectedDeckTheme.charAt(0).toUpperCase() + selectedDeckTheme.slice(1);
  updateThemeCards();
}
applyDeckTheme();
document.getElementById('export-pptx-option').addEventListener('click', exportPptx);
document.getElementById('export-pdf-option').addEventListener('click', exportPdf);
document.getElementById('btn-edit-slide').addEventListener('click', editCurrentSlide);
async function exportPdf() {
  if (!currentSlides.length) return;
  const btn = document.getElementById('export-pdf-option'); btn.disabled = true;
  try {
    const res = await fetch('/api/export-pdf', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({title:currentDeckTitle, slides:currentSlides})});
    if (!res.ok) { const data = await res.json().catch(()=>({})); throw new Error(data.error || 'PDF export failed'); }
    downloadBlob(await res.blob(), `${safeFileName(currentDeckTitle)}_pitch_deck.pdf`); closeModal('export-modal');
    pitchProgress.exported = true; updatePitchProgress(); showToast('PDF downloaded successfully.', 'success');
  } catch(err) { alert('PDF export error: ' + err.message); } finally { btn.disabled = false; }
}
async function editCurrentSlide() {
  const slide = currentSlides[currentSlideIndex]; if (!slide) return;
  const title = prompt('Slide title:', slide.title || ''); if (title === null) return;
  const subtitle = prompt('Slide subtitle:', slide.subtitle || ''); if (subtitle === null) return;
  const bullets = prompt('Bullet points (one per line):', (slide.bullets || []).join('\n')); if (bullets === null) return;
  const notes = prompt('Speaker notes:', slide.speaker_notes || ''); if (notes === null) return;
  slide.title = title.trim().slice(0,200); slide.subtitle = subtitle.trim().slice(0,250);
  slide.bullets = bullets.split('\n').map(x=>x.trim()).filter(Boolean).slice(0,10); slide.speaker_notes = notes.slice(0,3000);
  renderActiveSlide(); renderThumbnails();
  if (currentDeckId) {
    try { const res = await fetch(`/api/decks/${currentDeckId}`, {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({slides:currentSlides})}); if (!res.ok) throw new Error('Save failed'); showToast('Slide updated and saved.', 'success'); }
    catch(err) { showToast('Slide changed in this session, but saving failed.', 'warning'); }
  } else showToast('Slide updated for this session.', 'success');
}

document.getElementById('export-summary-option').addEventListener('click', downloadSummary);
async function exportPptx() {
  if (!currentSlides.length) return;
  const btn = document.getElementById('export-pptx-option');
  btn.disabled = true;
  btn.classList.add('working');
  try {
    const res = await fetch('/api/export-pptx', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: currentDeckTitle, slides: currentSlides, theme: selectedDeckTheme }) });
    if (!res.ok) throw new Error('Export failed');
    const blob = await res.blob();
    downloadBlob(blob, `${safeFileName(currentDeckTitle)}_pitch_deck.pptx`);
    closeModal('export-modal'); pitchProgress.exported = true; updatePitchProgress(); showToast('PowerPoint downloaded successfully.', 'success');
  } catch (err) { alert('Export error: ' + err.message); }
  finally { btn.disabled = false; btn.classList.remove('working'); }
}
function downloadSummary() {
  if (!currentSlides.length) return;
  let text = `${currentDeckTitle}\n${'='.repeat(currentDeckTitle.length)}\n\n`;
  currentSlides.forEach((s, i) => { text += `SLIDE ${i + 1}: ${s.title || ''}\n${s.subtitle || ''}\n`; (s.bullets || []).forEach(b => text += `• ${b}\n`); text += '\n'; });
  downloadBlob(new Blob([text], { type: 'text/plain;charset=utf-8' }), `${safeFileName(currentDeckTitle)}_summary.txt`);
  closeModal('export-modal'); pitchProgress.exported = true; updatePitchProgress(); showToast('Pitch summary downloaded.', 'success');
}
function downloadBlob(blob, filename) { const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
function safeFileName(name) { return String(name || 'pitch_deck').toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, ''); }

// #4 Practice My Pitch
const practiceTips = [
  'Open with the problem, then make the audience feel why it matters.',
  'Pause briefly after the key value proposition so it lands clearly.',
  'Use the metrics as proof points instead of reading every bullet.',
  'End with the outcome you want the audience to remember.'
];
let practicedSlides = new Set();
function buildPracticeScript(slide) {
  const bullets = (slide.bullets || []).slice(0, 3);
  const body = bullets.length ? bullets.join(' ') : (slide.subtitle || '');
  const title = slide.title || 'this part of the pitch';
  const opening = `Let me introduce ${title}.`;
  const key = slide.subtitle ? slide.subtitle : (body || 'This slide highlights an important part of the business idea.');
  const close = slide.speaker_notes || (bullets.length ? `The key takeaway is that ${bullets[0]}.` : 'The key takeaway is to connect this point back to the customer and business value.');
  return { opening, key, close };
}
function renderPractice() {
  if (!currentSlides.length) return;
  const slide = currentSlides[practiceIndex];
  const script = buildPracticeScript(slide);
  const bullets = (slide.bullets || []).slice(0, 3);
  document.getElementById('practice-slide-label').textContent = `Slide ${practiceIndex + 1} / ${currentSlides.length}`;
  document.getElementById('practice-status').textContent = practicedSlides.has(practiceIndex) ? '✓ Slide practiced' : 'Ready to rehearse';
  document.getElementById('practice-category').textContent = (slide.category || 'OVERVIEW').toUpperCase();
  document.getElementById('practice-slide-title').textContent = slide.title || 'Untitled slide';
  document.getElementById('practice-slide-subtitle').textContent = slide.subtitle || 'Focus on the main message of this slide.';
  const points = document.getElementById('practice-slide-points');
  points.innerHTML = '';
  bullets.forEach(b => { const li = document.createElement('li'); li.textContent = b; points.appendChild(li); });
  document.getElementById('practice-progress-text').textContent = `${practiceIndex + 1} / ${currentSlides.length}`;
  document.getElementById('practice-progress-bar').style.width = `${((practiceIndex + 1) / currentSlides.length) * 100}%`;
  document.getElementById('practice-script').innerHTML = `
    <div class="script-badge">🎙 SPEAKER SCRIPT</div>
    <h4>${escapeHtml(slide.title || 'Untitled slide')}</h4>
    <div class="script-section"><span class="script-section-label">Opening</span><p>${escapeHtml(script.opening)}</p></div>
    <div class="script-section"><span class="script-section-label">Key message</span><p>${escapeHtml(script.key)}</p></div>
    <div class="script-section"><span class="script-section-label">Close with</span><p>${escapeHtml(script.close)}</p></div>`;
  const tip = practiceTips[practiceIndex % practiceTips.length];
  document.getElementById('practice-tip').innerHTML = `<b>💡 Coach tip</b><span>${escapeHtml(tip)}</span>`;
  const mark = document.getElementById('practice-mark');
  mark.classList.toggle('done', practicedSlides.has(practiceIndex));
  mark.textContent = practicedSlides.has(practiceIndex) ? '✓ Slide practiced' : '○ Mark slide practiced';
  document.getElementById('practice-completed').textContent = `${practicedSlides.size} slide${practicedSlides.size === 1 ? '' : 's'} practiced`;
  document.getElementById('practice-prev').disabled = practiceIndex === 0;
  document.getElementById('practice-next').disabled = practiceIndex === currentSlides.length - 1;
}
function stopPracticeTimer() {
  if (practiceTimer) clearInterval(practiceTimer);
  practiceTimer = null;
  document.getElementById('practice-timer-btn').textContent = '▶ Start Practice';
  document.getElementById('practice-status').textContent = practicedSlides.has(practiceIndex) ? '✓ Slide practiced' : 'Paused — ready when you are';
}
function resetPracticeTimer() { stopPracticeTimer(); practiceSeconds = 0; document.getElementById('practice-timer').textContent = '00:00'; }
function formatTime(sec) { return `${String(Math.floor(sec / 60)).padStart(2,'0')}:${String(sec % 60).padStart(2,'0')}`; }
document.getElementById('btn-practice').addEventListener('click', () => { practiceIndex = currentSlideIndex; resetPracticeTimer(); renderPractice(); openModal('practice-modal'); });
document.getElementById('practice-prev').addEventListener('click', () => { if (practiceIndex > 0) { practiceIndex--; resetPracticeTimer(); renderPractice(); } });
document.getElementById('practice-next').addEventListener('click', () => { if (practiceIndex < currentSlides.length - 1) { practiceIndex++; resetPracticeTimer(); renderPractice(); } });
document.getElementById('practice-mark').addEventListener('click', () => {
  if (practicedSlides.has(practiceIndex)) practicedSlides.delete(practiceIndex); else practicedSlides.add(practiceIndex);
  renderPractice();
});
document.getElementById('practice-timer-btn').addEventListener('click', () => {
  if (practiceTimer) { stopPracticeTimer(); }
  else {
    document.getElementById('practice-timer-btn').textContent = '⏸ Pause Practice';
    document.getElementById('practice-status').textContent = '● Rehearsing this slide';
    practiceTimer = setInterval(() => { practiceSeconds++; document.getElementById('practice-timer').textContent = formatTime(practiceSeconds); }, 1000);
  }
});
document.getElementById('practice-modal').addEventListener('click', e => { if (e.target.id === 'practice-modal') { stopPracticeTimer(); closeModal('practice-modal'); } });

// #5 Smart Rewrite This Slide
let pendingRewrite = null;
function smartRewrite(slide) {
  const title = slide.title || 'Untitled slide';
  const subtitle = slide.subtitle || '';
  const bullets = (slide.bullets || []).map(b => {
    const clean = String(b).replace(/^[-•]\s*/, '').trim();
    if (/^(our|a|an|the)\b/i.test(clean)) return clean.replace(/\.$/, '') + ' — designed to deliver a clearer, faster and more scalable outcome.';
    return `Deliver ${clean.charAt(0).toLowerCase() + clean.slice(1).replace(/\.$/, '')} with a focused, measurable impact.`;
  });
  const strongerTitles = {
    problem: 'The Problem We Must Solve', solution: 'The Solution That Changes the Game', market: 'Who Needs This Most', features: 'What Makes the Product Powerful', market_size: 'The Opportunity Ahead', business_model: 'How the Business Creates Value', competitors: 'Our Competitive Advantage', marketing: 'How We Win Customers', roadmap: 'The Roadmap to Scale', ask: 'The Vision & Next Move', title: title
  };
  const newTitle = strongerTitles[slide.category] || `Why ${title} Matters`;
  const newSubtitle = subtitle ? `A sharper view of ${subtitle.toLowerCase().replace(/\.$/, '')}.` : 'Clear, concise and presentation-ready.';
  return { title: newTitle, subtitle: newSubtitle, bullets: bullets.slice(0, 4) };
}
function renderRewrite() {
  const slide = currentSlides[currentSlideIndex];
  pendingRewrite = smartRewrite(slide);
  document.getElementById('rewrite-current-title').textContent = slide.title || '';
  document.getElementById('rewrite-current-subtitle').textContent = slide.subtitle || '';
  document.getElementById('rewrite-current-bullets').innerHTML = (slide.bullets || []).slice(0,4).map(b => `<li>${escapeHtml(b)}</li>`).join('');
  document.getElementById('rewrite-new-title').textContent = pendingRewrite.title;
  document.getElementById('rewrite-new-subtitle').textContent = pendingRewrite.subtitle;
  document.getElementById('rewrite-new-bullets').innerHTML = pendingRewrite.bullets.map(b => `<li>${escapeHtml(b)}</li>`).join('');
}
document.getElementById('btn-rewrite').addEventListener('click', () => { renderRewrite(); openModal('rewrite-modal'); });
document.getElementById('btn-apply-rewrite').addEventListener('click', () => {
  if (!pendingRewrite || !currentSlides.length) return;
  Object.assign(currentSlides[currentSlideIndex], pendingRewrite);
  pitchProgress.refined = true; pitchProgress.exported = false; updatePitchProgress(); renderActiveSlide(); renderThumbnails(); closeModal('rewrite-modal'); showToast('✨ Slide rewritten successfully.', 'success');
});

// #10 Improve My Pitch: transparent rule-based feedback using the generated content.
document.getElementById('btn-improve').addEventListener('click', () => {
  const suggestions = buildPitchSuggestions();
  document.getElementById('improvement-list').innerHTML = suggestions.map((s, i) => `<div class="improvement-card"><span>${i + 1}</span><div><strong>${escapeHtml(s.title)}</strong><p>${escapeHtml(s.text)}</p></div></div>`).join('');
  openModal('improve-modal');
});
function buildPitchSuggestions() {
  const suggestions = [];
  const allText = currentSlides.map(s => `${s.title} ${(s.bullets || []).join(' ')}`).join(' ').toLowerCase();
  if (!allText.includes('customer') && !allText.includes('user')) suggestions.push({ title: 'Clarify the customer', text: 'Add a specific target customer or user segment so the audience immediately knows who benefits from the solution.' });
  if (!allText.includes('metric') && !allText.includes('kpi') && !allText.includes('%')) suggestions.push({ title: 'Add measurable proof', text: 'Include one or two measurable outcomes, such as time saved, cost reduction, adoption, accuracy, or growth targets.' });
  if (!allText.includes('roadmap') && !allText.includes('q1') && !allText.includes('milestone')) suggestions.push({ title: 'Strengthen the roadmap', text: 'Add clear near-term milestones to show how the idea moves from prototype to a real product.' });
  if (!allText.includes('different') && !allText.includes('advantage') && !allText.includes('moat')) suggestions.push({ title: 'Highlight differentiation', text: 'State what makes this solution different from existing alternatives and why users would switch.' });
  if (suggestions.length < 3) suggestions.push({ title: 'Make the opening stronger', text: 'Use a short, memorable one-line value proposition on the title slide to make the first impression stronger.' });
  return suggestions.slice(0, 4);
}

// #6 Theme
const savedTheme = localStorage.getItem('pitch-theme') || 'dark';
applyTheme(savedTheme);
document.getElementById('btn-theme').addEventListener('click', () => applyTheme(document.body.dataset.theme === 'light' ? 'dark' : 'light'));
function applyTheme(theme) { document.body.dataset.theme = theme; localStorage.setItem('pitch-theme', theme); document.getElementById('btn-theme').textContent = theme === 'light' ? '🌙' : '☀️'; }

// #9 Recent decks
async function loadRecentDecks() {
  const container = document.getElementById('recent-decks');
  try {
    const res = await fetch('/api/decks'); if (!res.ok) throw new Error('Unable to load recent decks');
    const decks = await res.json();
    if (!decks.length) { container.innerHTML = '<div class="recent-empty">No decks yet. Generate your first pitch deck above.</div>'; return; }
    container.innerHTML = decks.slice(0, 3).map(deck => {
      const date = deck.created_at ? new Date(deck.created_at).toLocaleDateString(undefined, { day: '2-digit', month: 'short' }) : '';
      return `<button class="recent-card" type="button" onclick="loadDeckFromHistory(${Number(deck.id)})"><span class="recent-icon">📊</span><span class="recent-info"><strong>${escapeHtml(deck.title || 'Untitled Deck')}</strong><small>${escapeHtml(deck.industry || 'General')} · ${escapeHtml(date)}</small></span><span class="recent-arrow">→</span></button>`;
    }).join('');
  } catch (err) { container.innerHTML = '<div class="recent-empty">Recent decks will appear here after your first generation.</div>'; }
}
document.getElementById('btn-refresh-recent').addEventListener('click', async () => {
  const btn = document.getElementById('btn-refresh-recent');
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = '↻ Refreshing...';
  await loadRecentDecks();
  btn.textContent = originalText;
  btn.disabled = false;
  showToast('Recent decks refreshed.', 'success');
});

// Deck History
const historyModal = document.getElementById('history-modal');
const historyList = document.getElementById('history-list');
document.getElementById('btn-view-history').addEventListener('click', async () => {
  historyModal.style.display = 'flex'; historyList.innerHTML = '<div class="history-loading"><span class="spinner"></span> Loading saved decks...</div>';
  try { const res = await fetch('/api/decks'); if (!res.ok) throw new Error('Unable to load deck history'); renderHistory(await res.json()); }
  catch (err) { historyList.innerHTML = `<div class="history-empty">❌ ${escapeHtml(err.message)}</div>`; }
});
document.getElementById('btn-close-history').addEventListener('click', closeHistory);
historyModal.addEventListener('click', e => { if (e.target === historyModal) closeHistory(); });
function closeHistory() { historyModal.style.display = 'none'; }
function renderHistory(decks) {
  if (!decks.length) { historyList.innerHTML = '<div class="history-empty">No generated decks found yet.</div>'; return; }
  historyList.innerHTML = decks.map(deck => `<button type="button" class="history-item" onclick="loadDeckFromHistory(${Number(deck.id)})"><span class="history-icon">📊</span><span class="history-item-main"><strong>${escapeHtml(deck.title || 'Untitled Deck')}</strong><span>${escapeHtml(deck.industry || 'General')}</span></span><small>${escapeHtml(deck.created_at ? new Date(deck.created_at).toLocaleString() : 'Unknown date')}</small><b>→</b></button>`).join('');
}
async function loadDeckFromHistory(deckId) {
  try {
    const res = await fetch(`/api/decks/${deckId}`); if (!res.ok) throw new Error('Unable to open this deck');
    const data = await res.json(); loadDeckIntoWorkspace(data); closeHistory(); document.getElementById('preview-card').scrollIntoView({ behavior: 'smooth', block: 'start' }); showToast('Deck loaded from history.', 'success');
  } catch (err) { alert('Error loading deck: ' + err.message); }
}

function openModal(id) { document.getElementById(id).style.display = 'flex'; }
function closeModal(id) { document.getElementById(id).style.display = 'none'; }
document.querySelectorAll('[data-close]').forEach(btn => btn.addEventListener('click', () => closeModal(btn.dataset.close)));
document.querySelectorAll('.overlay-modal').forEach(modal => modal.addEventListener('click', e => { if (e.target === modal) closeModal(modal.id); }));

function showToast(message, type = 'info') {
  const toast = document.createElement('div'); toast.className = `toast ${type}`; toast.textContent = message;
  document.getElementById('toast-container').appendChild(toast); setTimeout(() => toast.classList.add('show'), 20); setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 250); }, 2800);
}
function escapeHtml(value) { return String(value ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;'); }

loadRecentDecks();
