// Frontend JavaScript for Pitch Deck Generator
let currentSlides = [];
let currentSlideIndex = 0;
let currentDeckTitle = '';

const SAMPLES = [
  {
    companyName: 'MedPulse AI',
    industry: 'Healthcare & HealthTech',
    tagline: 'Predictive Remote Diagnostic Triage Powered by Clinical Machine Learning',
    problemStatement: 'Over 40% of emergency room visits could be prevented with early symptomatic detection, yet diagnostic delays cause avoidable complications and hospital resource burnout.',
    solutionDescription: 'An AI-powered continuous health analytics platform that ingests non-invasive biometric telemetry to flag acute deteriorations 12 hours prior to clinical onset.',
    businessModel: 'B2B SaaS subscription per hospital bed ($49/bed/month) + enterprise API licensing fees for regional healthcare systems.',
    competitors: 'Epic Systems, Teladoc Health'
  },
  {
    companyName: 'EcoTrack Logistics',
    industry: 'Supply Chain & CleanTech',
    tagline: 'Zero-Emission Autonomous Route Optimization for Commercial Freight Fleets',
    problemStatement: 'Commercial shipping generates 24% of global logistics carbon emissions, with empty deadhead miles costing operators over $28B in fuel waste annually.',
    solutionDescription: 'A dynamic AI dispatch system coordinating electric freight platoons, charging infrastructure stops, and algorithmic payload consolidation.',
    businessModel: 'Usage-based SaaS: 3.5% commission on verified freight fuel savings + monthly telematics subscription.',
    competitors: 'Convoy, Samsara Fleet'
  },
  {
    companyName: 'CodeCraft Mentor',
    industry: 'EdTech & Developer Tools',
    tagline: 'Interactive AI Pair-Programmer & Curriculum Engine for Computer Science Students',
    problemStatement: 'Computer science students struggle with algorithmic concepts (DSA, System Design) due to 1:60 student-to-professor ratios and sterile syntax checkers that do not explain logic.',
    solutionDescription: 'An adaptive AI tutor that analyzes code execution trees in real-time, visualizes data structures dynamically, and crafts custom practice problems matched to skill gaps.',
    businessModel: 'Freemium consumer tier ($9.99/month for Pro) + Institutional Enterprise campus licenses ($12,000/university/year).',
    competitors: 'LeetCode, GitHub Copilot'
  }
];

function loadSample(idx) {
  const sample = SAMPLES[idx];
  document.getElementById('companyName').value = sample.companyName;
  document.getElementById('industry').value = sample.industry;
  document.getElementById('tagline').value = sample.tagline;
  document.getElementById('problemStatement').value = sample.problemStatement;
  document.getElementById('solutionDescription').value = sample.solutionDescription;
  document.getElementById('businessModel').value = sample.businessModel;
  document.getElementById('competitors').value = sample.competitors;
}

document.getElementById('pitch-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('btn-generate');
  btn.disabled = true;
  btn.textContent = '⏳ Analyzing & Generating Pitch Deck...';

  const payload = {
    companyName: document.getElementById('companyName').value,
    industry: document.getElementById('industry').value,
    tagline: document.getElementById('tagline').value,
    problemStatement: document.getElementById('problemStatement').value,
    solutionDescription: document.getElementById('solutionDescription').value,
    businessModel: document.getElementById('businessModel').value,
    competitors: document.getElementById('competitors').value
  };

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.slides) {
      currentSlides = data.slides;
      currentDeckTitle = data.title;
      currentSlideIndex = 0;
      renderActiveSlide();
      renderThumbnails();
      document.getElementById('empty-state').style.display = 'none';
      document.getElementById('active-slide-view').style.display = 'flex';
      document.getElementById('carousel-controls').style.display = 'flex';
      document.getElementById('thumbnails-strip').style.display = 'flex';
      document.getElementById('btn-export-pptx').disabled = false;
      document.getElementById('deck-title-display').textContent = data.title + ' Pitch Deck';
      document.getElementById('deck-slide-count').textContent = currentSlides.length + ' Slides Generated';
    }
  } catch (err) {
    alert('Error generating pitch deck: ' + err);
  } finally {
    btn.disabled = false;
    btn.textContent = '✨ Generate AI Pitch Deck';
  }
});

function renderActiveSlide() {
  if (!currentSlides.length) return;
  const slide = currentSlides[currentSlideIndex];
  
  document.getElementById('slide-category').textContent = (slide.category || 'OVERVIEW').toUpperCase();
  document.getElementById('slide-title').textContent = slide.title || '';
  document.getElementById('slide-subtitle').textContent = slide.subtitle || '';
  document.getElementById('slide-speaker-notes').textContent = slide.speaker_notes || 'None';
  document.getElementById('slide-indicator').textContent = `Slide ${currentSlideIndex + 1} / ${currentSlides.length}`;

  const bulletsList = document.getElementById('slide-bullets');
  bulletsList.innerHTML = '';
  (slide.bullets || []).forEach(b => {
    const li = document.createElement('li');
    li.textContent = b;
    bulletsList.appendChild(li);
  });

  const metricsBox = document.getElementById('slide-metrics');
  metricsBox.innerHTML = '';
  (slide.metrics || []).forEach(m => {
    const div = document.createElement('div');
    div.className = 'metric-box';
    div.innerHTML = `<div class="metric-val">${m.value}</div><div class="metric-lbl">${m.label}</div>`;
    metricsBox.appendChild(div);
  });

  // Highlight thumbnail
  document.querySelectorAll('.thumb-card').forEach((el, idx) => {
    el.classList.toggle('active', idx === currentSlideIndex);
  });
}

function renderThumbnails() {
  const strip = document.getElementById('thumbnails-strip');
  strip.innerHTML = '';
  currentSlides.forEach((s, idx) => {
    const thumb = document.createElement('div');
    thumb.className = 'thumb-card' + (idx === currentSlideIndex ? ' active' : '');
    thumb.textContent = (idx + 1) + '. ' + s.title;
    thumb.onclick = () => {
      currentSlideIndex = idx;
      renderActiveSlide();
    };
    strip.appendChild(thumb);
  });
}

document.getElementById('btn-prev').addEventListener('click', () => {
  if (currentSlideIndex > 0) {
    currentSlideIndex--;
    renderActiveSlide();
  }
});

document.getElementById('btn-next').addEventListener('click', () => {
  if (currentSlideIndex < currentSlides.length - 1) {
    currentSlideIndex++;
    renderActiveSlide();
  }
});

document.getElementById('btn-export-pptx').addEventListener('click', async () => {
  if (!currentSlides.length) return;
  const btn = document.getElementById('btn-export-pptx');
  btn.textContent = '⏳ Creating .pptx...';
  btn.disabled = true;

  try {
    const res = await fetch('/api/export-pptx', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: currentDeckTitle,
        slides: currentSlides
      })
    });
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentDeckTitle.toLowerCase().replace(/\s+/g, '_')}_pitch_deck.pptx`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  } catch (err) {
    alert('Export error: ' + err);
  } finally {
    btn.textContent = '📥 Export PowerPoint (.pptx)';
    btn.disabled = false;
  }
});
