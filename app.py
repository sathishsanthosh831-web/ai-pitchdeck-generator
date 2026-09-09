import os
import json
from datetime import datetime
from io import BytesIO
from flask import Flask, render_template, request, jsonify, send_file, session
from flask_cors import CORS
from models import db, User, PitchDeck, Slide
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'pitchdeck-secret-key-bsc-cs-2026')

# Use PostgreSQL (Render) via DATABASE_URL if present, otherwise fall back to local SQLite for dev
_db_url = os.getenv('DATABASE_URL', 'sqlite:///pitchdecks.db')
# Render's DATABASE_URL sometimes starts with postgres:// which SQLAlchemy no longer accepts
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db.init_app(app)

with app.app_context():
    db.create_all()

# ----------------- AI PITCH GENERATOR LOGIC -----------------
def generate_ai_pitch_deck(data):
    company = data.get('companyName', 'InnovateAI')
    industry = data.get('industry', 'Technology')
    tagline = data.get('tagline', 'Revolutionizing industry workflows with AI')
    problem = data.get('problemStatement', 'Manual latency and fragmented tools create massive operational overhead.')
    solution = data.get('solutionDescription', 'An autonomous AI platform that delivers end-to-end workflow intelligence.')
    target = data.get('targetAudience', 'Enterprise leaders, mid-market operators, and high-growth startups.')
    model = data.get('businessModel', 'B2B SaaS subscription with tier-based usage pricing.')
    competitors = data.get('competitors', 'Legacy incumbents and manual point solutions')

    slides = [
        {
            "category": "title",
            "title": company,
            "subtitle": tagline,
            "bullets": [
                f"Sector: {industry}",
                "Enterprise Architecture & Defensible Unit Economics",
                "High-Margin Scalable Software Architecture"
            ],
            "metrics": [{"label": "Market Stage", "value": "Go-To-Market Ready"}, {"label": "Target Model", "value": "High Scalability"}],
            "speaker_notes": f"Welcome. Today we introduce {company}. Our mission is {tagline}."
        },
        {
            "category": "problem",
            "title": "The Market Problem",
            "subtitle": "Critical Inefficiencies in Existing Workflows",
            "bullets": [
                problem,
                "Disconnected legacy software tools require heavy manual intervention.",
                "Enterprises lose hundreds of productive hours to unautomated bottlenecks."
            ],
            "metrics": [{"label": "Lost Value", "value": "42%"}, {"label": "Latency", "value": "3.4x Slower"}],
            "speaker_notes": f"The core pain point is clear: {problem}."
        },
        {
            "category": "solution",
            "title": "Our AI Solution",
            "subtitle": f"{company}: The Intelligent Operating Standard",
            "bullets": [
                solution,
                "Seamless integration with existing enterprise data pipelines.",
                "Delivers real-time autonomous recommendations and actionable insights.",
                "Built for 99.9% uptime with bank-grade security compliance."
            ],
            "metrics": [{"label": "Efficiency", "value": "+75%"}, {"label": "ROI Timeline", "value": "< 60 Days"}],
            "speaker_notes": f"Our proprietary platform resolves this problem: {solution}."
        },
        {
            "category": "market",
            "title": "Target Audience & ICP",
            "subtitle": "Precision Customer Segmentation",
            "bullets": [
                f"Ideal Customer Profile: {target}",
                "Mid-market enterprises requiring fast deployment without overhead.",
                "High-volume institutions with expanding annual digital budgets."
            ],
            "metrics": [{"label": "Target Accounts", "value": "45,000+"}, {"label": "Willingness to Pay", "value": "High"}],
            "speaker_notes": f"We target {target} who are actively seeking modernization."
        },
        {
            "category": "features",
            "title": "Core Product Features",
            "subtitle": "Key Technological Advantages",
            "bullets": [
                "Autonomous AI Workflow Processing Engine.",
                "Real-time Telemetry & Dynamic Metric Dashboards.",
                "Universal API Connectors for Instant Data Ingestion.",
                "Role-Based Access Control (RBAC) and Audit Logs."
            ],
            "metrics": [{"label": "Latency", "value": "< 250ms"}, {"label": "Accuracy", "value": "98.6%"}],
            "speaker_notes": "The architecture is modular, fast, and engineered for high throughput."
        },
        {
            "category": "market_size",
            "title": "Market Opportunity (TAM/SAM/SOM)",
            "subtitle": "Massive Addressable Market Horizon",
            "bullets": [
                f"Total Addressable Market (TAM): Global {industry} software expenditures.",
                "Serviceable Addressable Market (SAM): Digital cloud-first adoption segment.",
                "Serviceable Obtainable Market (SOM): 3-year targeted capture."
            ],
            "metrics": [{"label": "TAM", "value": "$48.5 B"}, {"label": "SAM", "value": "$12.2 B"}, {"label": "SOM (Year 3)", "value": "$180 M"}],
            "speaker_notes": "We are operating in a multi-billion dollar expanding market."
        },
        {
            "category": "business_model",
            "title": "Business & Monetization Model",
            "subtitle": "High Gross-Margin Unit Economics",
            "bullets": [
                f"Core Strategy: {model}",
                "Self-serve starter tier for rapid user acquisition.",
                "Enterprise annual recurring contracts with custom SLA guarantees."
            ],
            "metrics": [{"label": "Gross Margin", "value": "82%"}, {"label": "LTV:CAC", "value": "4.2x"}],
            "speaker_notes": f"Monetization is based on {model} with strong capital efficiency."
        },
        {
            "category": "competitors",
            "title": "Competitive Matrix & Moat",
            "subtitle": "Why We Win Over Existing Options",
            "bullets": [
                f"Legacy Competitors: {competitors}",
                "Incumbents are slow, expensive, and require months of consulting.",
                "Our Moat: Proprietary AI logic, self-learning loops, and instant onboarding."
            ],
            "metrics": [{"label": "Setup Time", "value": "15 Mins"}, {"label": "Cost Savings", "value": "80% Lower"}],
            "speaker_notes": f"Compared to {competitors}, our solution is faster, modern, and cost-effective."
        },
        {
            "category": "marketing",
            "title": "Go-To-Market Strategy",
            "subtitle": "Customer Acquisition Flywheel",
            "bullets": [
                "Product-Led Growth (PLG) trial converts bottom-up adopters.",
                "Targeted Account-Based Marketing (ABM) for enterprise buyers.",
                "Strategic marketplace partnerships and developer advocacy."
            ],
            "metrics": [{"label": "CAC Payback", "value": "< 5 Mos"}, {"label": "Viral Factor", "value": "1.35x"}],
            "speaker_notes": "Our flywheel couples self-serve viral adoption with direct outbound sales."
        },
        {
            "category": "roadmap",
            "title": "Product Roadmap & Milestones",
            "subtitle": "Disciplined Execution Over 18 Months",
            "bullets": [
                "Q1: Launch core platform with initial 25 enterprise pilot users.",
                "Q2: Deploy public API ecosystem and achieve SOC-2 compliance.",
                "Q3: Roll out autonomous multi-agent workflows.",
                "Q4: Global expansion targeting $1.2M Annual Recurring Revenue (ARR)."
            ],
            "metrics": [{"label": "Q2 ARR Target", "value": "$250 K"}, {"label": "Year 1 Target", "value": "$1.2 M"}],
            "speaker_notes": "We have an execution roadmap driven by clear milestones."
        },
        {
            "category": "ask",
            "title": "Vision & Strategic Growth",
            "subtitle": f"Join Us in Shaping the Future of {industry}",
            "bullets": [
                "Strategic Acceleration: Focused on product innovation, customer acquisition, and enterprise rollout.",
                "Resource Allocation: 50% Engineering & AI, 30% Go-To-Market & Partnerships, 20% Operations.",
                "Target Milestones: 250 enterprise accounts and $1.5M+ ARR within 18 months."
            ],
            "metrics": [{"label": "Target Horizon", "value": "18 Months"}, {"label": "Scale Potential", "value": "10x Growth"}],
            "speaker_notes": f"We are uniquely positioned to lead {industry}. Thank you."
        }
    ]
    return slides

# ----------------- FLASK WEB ROUTES -----------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.json or {}
    slides_data = generate_ai_pitch_deck(data)
    
    # Save to SQLite/MySQL
    deck = PitchDeck(
        title=data.get('companyName', 'InnovateAI'),
        industry=data.get('industry', 'Tech'),
        tagline=data.get('tagline', ''),
        theme='midnight',
        created_at=datetime.utcnow()
    )
    db.session.add(deck)
    db.session.commit()

    for idx, s in enumerate(slides_data):
        slide = Slide(
            deck_id=deck.id,
            category=s.get('category'),
            title=s.get('title'),
            subtitle=s.get('subtitle', ''),
            bullets_json=json.dumps(s.get('bullets', [])),
            metrics_json=json.dumps(s.get('metrics', [])),
            speaker_notes=s.get('speaker_notes', ''),
            order_index=idx
        )
        db.session.add(slide)
    db.session.commit()

    return jsonify({
        "success": True,
        "deck_id": deck.id,
        "title": deck.title,
        "industry": deck.industry,
        "slides": slides_data
    })

@app.route('/api/export-pptx', methods=['POST'])
def export_pptx():
    """Generates real Microsoft PowerPoint (.pptx) file using python-pptx"""
    data = request.json or {}
    title = data.get('title', 'Pitch_Deck')
    slides_list = data.get('slides', [])

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    blank_layout = prs.slide_layouts[6]

    for idx, slide_info in enumerate(slides_list):
        slide = prs.slides.add_slide(blank_layout)

        # Background fill
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor(15, 23, 42) # Slate-900

        # Slide Number and Category
        header_box = slide.shapes.add_textbox(Inches(1.0), Inches(0.6), Inches(11.3), Inches(0.4))
        tf_h = header_box.text_frame
        tf_h.text = f"SLIDE {idx + 1} OF {len(slides_list)} • {slide_info.get('category', 'OVERVIEW').upper()}"
        p_h = tf_h.paragraphs[0]
        p_h.font.size = Pt(11)
        p_h.font.bold = True
        p_h.font.color.rgb = RGBColor(129, 140, 248) # Indigo-400

        # Title
        title_box = slide.shapes.add_textbox(Inches(1.0), Inches(1.0), Inches(11.3), Inches(0.8))
        tf_t = title_box.text_frame
        tf_t.word_wrap = True
        tf_t.text = slide_info.get('title', '')
        p_t = tf_t.paragraphs[0]
        p_t.font.size = Pt(28)
        p_t.font.bold = True
        p_t.font.color.rgb = RGBColor(255, 255, 255)

        # Subtitle
        if slide_info.get('subtitle'):
            sub_box = slide.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(0.5))
            tf_s = sub_box.text_frame
            tf_s.text = slide_info.get('subtitle')
            p_s = tf_s.paragraphs[0]
            p_s.font.size = Pt(14)
            p_s.font.italic = True
            p_s.font.color.rgb = RGBColor(148, 163, 184)

        # Bullet Points
        bullets = slide_info.get('bullets', [])
        if bullets:
            content_box = slide.shapes.add_textbox(Inches(1.0), Inches(2.5), Inches(8.0), Inches(4.2))
            tf_c = content_box.text_frame
            tf_c.word_wrap = True
            for b_idx, bullet in enumerate(bullets):
                p_b = tf_c.add_paragraph() if b_idx > 0 else tf_c.paragraphs[0]
                p_b.text = f"•  {bullet}"
                p_b.font.size = Pt(16)
                p_b.font.color.rgb = RGBColor(226, 232, 240)
                p_b.space_after = Pt(14)

        # Metrics Sidebar
        metrics = slide_info.get('metrics', [])
        for m_idx, m in enumerate(metrics):
            m_y = 2.5 + (m_idx * 1.6)
            m_box = slide.shapes.add_textbox(Inches(9.4), Inches(m_y), Inches(3.0), Inches(1.3))
            tf_m = m_box.text_frame
            p_val = tf_m.paragraphs[0]
            p_val.text = str(m.get('value', ''))
            p_val.font.size = Pt(24)
            p_val.font.bold = True
            p_val.font.color.rgb = RGBColor(56, 189, 248) # Sky-400

            p_lbl = tf_m.add_paragraph()
            p_lbl.text = str(m.get('label', ''))
            p_lbl.font.size = Pt(12)
            p_lbl.font.bold = True
            p_lbl.font.color.rgb = RGBColor(255, 255, 255)

        # Speaker notes
        if slide_info.get('speaker_notes'):
            notes_slide = slide.notes_slide
            text_frame = notes_slide.notes_text_frame
            text_frame.text = slide_info.get('speaker_notes')

    output = BytesIO()
    prs.save(output)
    output.seek(0)

    filename = f"{title.replace(' ', '_').lower()}_pitch_deck.pptx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation')

@app.route('/api/decks', methods=['GET'])
def get_decks():
    decks = PitchDeck.query.order_by(PitchDeck.created_at.desc()).limit(10).all()
    results = []
    for d in decks:
        results.append({
            "id": d.id,
            "title": d.title,
            "industry": d.industry,
            "created_at": d.created_at.isoformat()
        })
    return jsonify(results)

if __name__ == '__main__':
    print("AI Pitch Deck Generator is starting on http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
