import os
import json
import re
from datetime import datetime
from io import BytesIO
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from functools import wraps
from models import db, User, PitchDeck, Slide
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY') or os.urandom(32).hex()
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

# Google OAuth credentials are configured as environment variables on Render.
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('google_user'):
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Please sign in with Google first.'}), 401
            return redirect(url_for('index'))
        return view(*args, **kwargs)
    return wrapped

@app.before_request
def protect_api_routes():
    # Health checks remain public for Render; app APIs require a signed-in session.
    if request.path.startswith('/api/') and request.path not in ('/api/health',):
        if not session.get('google_user'):
            return jsonify({'error': 'Please sign in with Google first.'}), 401


# Use PostgreSQL (Render) via DATABASE_URL if present, otherwise fall back to local SQLite for dev
_db_url = os.getenv('DATABASE_URL', 'sqlite:///pitchdecks.db')
# Normalize Render PostgreSQL URLs to the psycopg 3 driver used in requirements.txt.
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql+psycopg://', 1)
elif _db_url.startswith('postgresql://'):
    _db_url = _db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
elif _db_url.startswith('postgresql+psycopg2://'):
    _db_url = _db_url.replace('postgresql+psycopg2://', 'postgresql+psycopg://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db.init_app(app)

with app.app_context():
    db.create_all()

# ----------------- AI PITCH GENERATOR LOGIC -----------------
def generate_template_pitch_deck(data):
    """Build the deck directly from the user's five inputs.

    This version deliberately avoids invented facts, generic business claims,
    unsupported statistics, or unrelated feature descriptions. Every content
    slide is grounded in the information supplied by the user.
    """
    company = (data.get('companyName') or '').strip() or 'My Project'
    industry = (data.get('industry') or '').strip() or 'General'
    tagline = (data.get('tagline') or '').strip() or 'A solution designed around a real user need.'
    problem = (data.get('problemStatement') or '').strip() or 'The user has identified a problem that needs a better solution.'
    solution = (data.get('solutionDescription') or '').strip() or 'The proposed solution is designed to address the stated problem.'
    target = (data.get('targetAudience') or '').strip() or 'The target users identified by the project.'

    def sentences(text):
        """Split user text into readable points without changing its meaning."""
        import re
        parts = [x.strip(' \t\n•-') for x in re.split(r'(?<=[.!?])\s+|\n+', text) if x.strip()]
        return parts or [text.strip()]

    problem_points = sentences(problem)
    solution_points = sentences(solution)

    # Use the user's own wording wherever possible. The remaining text only
    # provides slide structure; it does not claim facts that were not entered.
    problem_bullets = problem_points[:4]
    solution_bullets = solution_points[:4]

    how_it_works = [
        f"The user identifies the need: {problem_points[0]}",
        f"The proposed idea addresses it: {solution_points[0]}",
        f"The solution is intended for: {target}"
    ]

    key_points = solution_points[:4]
    benefits = [
        f"Addresses the stated problem: {problem_points[0]}",
        f"Provides the proposed solution: {solution_points[0]}",
        f"Designed for the stated audience: {target}"
    ]

    future_points = [
        "Improve and refine the solution based on user feedback.",
        "Add features that support the same problem and target audience.",
        "Expand the project only where it remains relevant to the stated idea."
    ]

    # Real numbers computed from the user's own input - not invented business
    # claims. These are honest, verifiable counts (word counts, point counts),
    # so the metric sidebar on each slide still shows a calculated figure.
    problem_word_count = len(problem.split())
    solution_word_count = len(solution.split())
    problem_point_count = len(problem_points)
    solution_point_count = len(solution_points)
    key_point_count = len(key_points)
    benefit_count = len(benefits)
    future_point_count = len(future_points)
    roadmap_steps = [
        "Step 1: Finalize the problem and target users.",
        "Step 2: Develop and test the proposed solution.",
        "Step 3: Collect user feedback and improve the solution.",
        "Step 4: Expand only with relevant features."
    ]
    conclusion_bullets = [
        f"Project: {company}",
        f"Problem: {problem_points[0]}",
        f"Solution: {solution_points[0]}",
        f"Target users: {target}"
    ]
    total_slides = 11

    slides = [
        {
            "category": "title",
            "title": company,
            "subtitle": tagline,
            "bullets": [f"Industry: {industry}", f"Target audience: {target}"],
            "metrics": [{"label": "Industry", "value": industry[:24]}, {"label": "Slides", "value": str(total_slides)}],
            "speaker_notes": f"Hello everyone. Today I am presenting {company}. {tagline} The project is for {target}."
        },
        {
            "category": "problem",
            "title": "The Problem",
            "subtitle": "The problem described in your input",
            "bullets": problem_bullets,
            "metrics": [{"label": "Points raised", "value": str(problem_point_count)}, {"label": "Words", "value": str(problem_word_count)}],
            "speaker_notes": f"The problem we want to address is: {problem}"
        },
        {
            "category": "solution",
            "title": "Our Solution",
            "subtitle": "The solution described in your input",
            "bullets": solution_bullets,
            "metrics": [{"label": "Points raised", "value": str(solution_point_count)}, {"label": "Words", "value": str(solution_word_count)}],
            "speaker_notes": f"Our proposed solution is: {solution}"
        },
        {
            "category": "how_it_works",
            "title": "How It Works",
            "subtitle": "The idea in a simple flow",
            "bullets": how_it_works,
            "metrics": [{"label": "Step 1", "value": "Problem"}, {"label": "Step 2", "value": "Solution"}, {"label": "Step 3", "value": "Users"}],
            "speaker_notes": "This slide connects the problem, the proposed solution, and the target users using only the information provided."
        },
        {
            "category": "audience",
            "title": "Who Can Use It?",
            "subtitle": "The target audience you entered",
            "bullets": [target, f"Industry / area: {industry}"],
            "metrics": [{"label": "Audience", "value": target[:24]}, {"label": "Industry", "value": industry[:24]}],
            "speaker_notes": f"The target audience for this project is {target}. The project is related to {industry}."
        },
        {
            "category": "market_analysis",
            "title": "Market & Impact Analysis",
            "subtitle": "Input-based analysis; no unsupported market statistics",
            "bullets": ([
                f"Target market entered: {data.get('targetMarket', '').strip()}",
                f"Known user base entered: {data.get('knownUserBase', '').strip()} users" if str(data.get('knownUserBase', '')).strip().isdigit() else "Known user base: not provided, so a reliable user-count calculation is not possible.",
                "Calculation basis: use only the market/user figures supplied by the project owner; verify any external figures before presenting them.",
                "Impact measurement: track users reached, successful task completions, time saved, and feedback during a defined test period."
            ] if str(data.get('targetMarket', '')).strip() or str(data.get('knownUserBase', '')).strip() else [
                "Target market size: insufficient input to calculate a reliable estimate.",
                "Known user base: not provided; no user-count estimate is invented.",
                "To calculate reach: verified eligible users × expected adoption rate = estimated users; both inputs must be documented.",
                "Impact measurement: track users reached, successful task completions, time saved, and feedback during a defined test period."
            ]),
            "metrics": ([{"label": "Known users", "value": str(int(data.get('knownUserBase', '0')))}] if str(data.get('knownUserBase', '')).strip().isdigit() else [{"label": "Market data", "value": "Not provided"}]),
            "speaker_notes": "Explain that market sizing is only reliable when the eligible market and assumptions have a verifiable source. Do not present illustrative estimates as facts. If a known user base was supplied, identify it as user-provided input rather than independently verified data."
        },
        {
            "category": "features",
            "title": "Key Points of the Solution",
            "subtitle": "Important points taken from your solution description",
            "bullets": key_points,
            "metrics": [{"label": "Key points", "value": str(key_point_count)}],
            "speaker_notes": "These points are taken directly from the solution description entered by the user."
        },
        {
            "category": "benefits",
            "title": "Expected Value",
            "subtitle": "What the proposed idea is intended to address",
            "bullets": benefits,
            "metrics": [{"label": "Value points", "value": str(benefit_count)}],
            "speaker_notes": "This slide does not invent benefits. It connects the expected value only to the problem, solution, and audience provided."
        },
        {
            "category": "opportunity",
            "title": "Future Opportunity",
            "subtitle": "Possible next steps for the same idea",
            "bullets": future_points,
            "metrics": [{"label": "Next steps", "value": str(future_point_count)}],
            "speaker_notes": "Future improvements should remain connected to the original problem, solution, and target audience."
        },
        {
            "category": "roadmap",
            "title": "Development Roadmap",
            "subtitle": "A simple project path",
            "bullets": roadmap_steps,
            "metrics": [{"label": "Phases", "value": str(len(roadmap_steps))}],
            "speaker_notes": "The roadmap keeps development focused on the problem, solution, users, testing, and relevant improvements."
        },
        {
            "category": "conclusion",
            "title": "Final Takeaway",
            "subtitle": "Your idea in one clear message",
            "bullets": conclusion_bullets,
            "metrics": [{"label": "Summary points", "value": str(len(conclusion_bullets))}],
            "speaker_notes": f"To conclude, {company} focuses on this problem: {problem_points[0]} The proposed solution is: {solution_points[0]} It is intended for: {target}. Thank you."
        }
    ]
    return slides

def generate_ai_pitch_deck(data):
    """Use Anthropic Claude when configured; otherwise keep the deterministic local generator available."""
    api_key = os.getenv('ANTHROPIC_API_KEY', '').strip()
    if not api_key:
        return generate_template_pitch_deck(data)
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key, timeout=35.0, max_retries=1)
        prompt_data = {k: str(data.get(k, '') or '')[:4000] for k in
                       ('companyName','industry','tagline','problemStatement','solutionDescription','targetAudience','targetMarket','knownUserBase')}
        response = client.messages.create(
            model=os.getenv('ANTHROPIC_MODEL', 'claude-3-5-haiku-latest'),
            max_tokens=4500,
            system=("You create presentation-ready startup pitch decks for a student presenting to faculty. "
                    "Use the user's inputs carefully. Return ONLY valid JSON: an array of 9-11 objects. Each object "
                    "must contain category, title, subtitle, bullets (array of strings), metrics (array of objects "
                    "with label/value), and speaker_notes. Include title, problem, solution, audience, features, "
                    "value, roadmap, conclusion, and one dedicated 'market_analysis' slide. On that slide, quantify "
                    "the problem, explain how the proposed solution could improve it, and estimate potential users "
                    "when reasonable. Show the calculation formula, assumptions, timeframe, and source basis in the "
                    "bullets or speaker notes. If geography or a known user base is missing, say the estimate is "
                    "illustrative and provide a cautious range only when defensible; otherwise clearly say there is "
                    "not enough information to calculate a reliable count. Never invent sourced facts, official "
                    "statistics, market sizes, customers, revenue, or precise outcomes. Do not present assumptions as "
                    "verified data. Mark estimates as 'Illustrative estimate' and include confidence/limitations. "
                    "Any calculated value must show its formula and inputs; do not give unsupported precise numbers."),
            messages=[{"role":"user","content":"Create a pitch deck from these inputs:\n" + json.dumps(prompt_data, ensure_ascii=False)}]
        )
        text = ''.join(block.text for block in response.content if getattr(block, 'type', '') == 'text').strip()
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text, flags=re.I)
        slides = json.loads(text)
        if not isinstance(slides, list) or not 5 <= len(slides) <= 12:
            raise ValueError('Unexpected slide structure')
        clean=[]
        for item in slides:
            if not isinstance(item, dict) or not item.get('title'): continue
            clean.append({
                'category': str(item.get('category','content'))[:50],
                'title': str(item.get('title',''))[:200],
                'subtitle': str(item.get('subtitle',''))[:250],
                'bullets': [str(x)[:800] for x in item.get('bullets',[])[:8]],
                'metrics': [{'label':str(m.get('label',''))[:60], 'value':str(m.get('value',''))[:80]} for m in item.get('metrics',[])[:4] if isinstance(m,dict)],
                'speaker_notes': str(item.get('speaker_notes',''))[:2000]
            })
        if len(clean) < 5: raise ValueError('Too few valid slides')
        return clean
    except Exception as exc:
        app.logger.warning('Claude generation unavailable; using local generator: %s', exc)
        return generate_template_pitch_deck(data)

# ----------------- OPTIONAL ADVANCED PLANNING CALCULATIONS -----------------
def _optional_number(data, key, label, minimum=0):
    raw = str(data.get(key, '') or '').strip().replace(',', '')
    if not raw:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValueError(f'{label} must be a valid number')
    if value < minimum:
        raise ValueError(f'{label} must be at least {minimum}')
    return value

def build_advanced_planning_slide(data):
    """Return a transparent, assumption-based slide only when advanced inputs exist."""
    fields = {
        'monthlyPrice': 'Monthly price per paying customer',
        'monthlyCosts': 'Monthly operating costs',
        'customerVariableCost': 'Variable cost per customer/month',
        'monthlyMarketing': 'Monthly marketing spend',
        'newCustomersMonthly': 'New paying customers per month',
        'marketCustomers': 'Eligible target-market customers',
        'marketPenetration': 'Expected market capture percentage',
    }
    if not any(str(data.get(k, '') or '').strip() for k in fields):
        return None
    values = {k: _optional_number(data, k, label, 0) for k, label in fields.items()}
    price = values['monthlyPrice']
    costs = values['monthlyCosts']
    variable = values['customerVariableCost']
    marketing = values['monthlyMarketing']
    new_customers = values['newCustomersMonthly']
    market_customers = values['marketCustomers']
    penetration = values['marketPenetration']
    if penetration is not None and penetration > 100:
        raise ValueError('Expected market capture percentage must be between 0 and 100')
    if new_customers is not None and not new_customers.is_integer():
        raise ValueError('New paying customers per month must be a whole number')
    if market_customers is not None and not market_customers.is_integer():
        raise ValueError('Eligible target-market customers must be a whole number')
    bullets=[]; metrics=[]
    if price is not None:
        bullets.append(f'MRR scenario = monthly paying customers × monthly price. Monthly price entered: {price:,.2f}; customer count must be supplied to calculate actual MRR.')
        metrics.append({'label':'Monthly price','value':f'{price:,.2f}'})
    if price is not None and variable is not None:
        contribution = price - variable
        bullets.append(f'Contribution per customer = price − variable cost = {price:,.2f} − {variable:,.2f} = {contribution:,.2f} per month.')
        metrics.append({'label':'Contribution/customer','value':f'{contribution:,.2f}'})
        if costs is not None:
            if contribution > 0:
                breakeven = int(__import__('math').ceil(costs / contribution))
                bullets.append(f'Estimated break-even customers = ceiling(monthly operating costs ÷ contribution) = ceiling({costs:,.2f} ÷ {contribution:,.2f}) = {breakeven} paying customers.')
                metrics.append({'label':'Break-even customers','value':str(breakeven)})
            else:
                bullets.append('Break-even customer count cannot be calculated because contribution per customer is zero or negative.')
    if costs is not None:
        bullets.append(f'Monthly operating costs entered: {costs:,.2f}. This is an input assumption, not independently verified.')
    if marketing is not None and new_customers is not None:
        if new_customers > 0:
            cac = marketing / new_customers
            bullets.append(f'Estimated CAC = monthly marketing spend ÷ new paying customers = {marketing:,.2f} ÷ {new_customers:,.0f} = {cac:,.2f} per new customer.')
            metrics.append({'label':'Estimated CAC','value':f'{cac:,.2f}'})
        else:
            bullets.append('CAC not calculated because new paying customers per month is zero.')
    if market_customers is not None and penetration is not None:
        captured = market_customers * penetration / 100
        bullets.append(f'Illustrative target-market capture = eligible customers × capture rate = {market_customers:,.0f} × {penetration:g}% = {captured:,.1f} customers (scenario only; validate both inputs).')
        metrics.append({'label':'Illustrative capture','value':f'{captured:,.1f}'})
    if price is not None and costs is not None:
        bullets.append('Monthly operating surplus cannot be calculated without the number of paying customers; once supplied, calculate (paying customers × price) − operating costs.')
    bullets.append('These are scenario calculations from user-entered assumptions, not forecasts or verified market facts. Currency is whatever currency the user intended for the entered amounts.')
    return {
        'category':'advanced_planning',
        'title':'Advanced Planning & Financial Scenarios',
        'subtitle':'Transparent calculations from the assumptions you entered',
        'bullets':bullets[:8],
        'metrics':metrics[:4] or [{'label':'Scenario inputs','value':str(sum(v is not None for v in values.values()))}],
        'speaker_notes':'Explain that each result is formula-based and depends on user-entered assumptions. Confirm the currency, time period, customer definition, and evidence for market estimates before presenting. CAC is only calculated when marketing spend and new paying customers are supplied; break-even requires positive contribution per customer.'
    }

# ----------------- FLASK WEB ROUTES -----------------
@app.route('/')
def index():
    if session.get('google_user'):
        return redirect(url_for('workspace'))
    return render_template('login.html')

@app.route('/login/google')
def login_google():
    if not os.getenv('GOOGLE_CLIENT_ID') or not os.getenv('GOOGLE_CLIENT_SECRET'):
        return render_template('login.html', config_error=True), 503
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def google_callback():
    try:
        token = google.authorize_access_token()
        userinfo = token.get('userinfo')
        if not userinfo:
            userinfo = google.userinfo()
        if not userinfo or not userinfo.get('email'):
            return render_template('login.html', auth_error='Google did not return an email address.'), 400
        session['google_user'] = {
            'name': userinfo.get('name') or userinfo.get('given_name') or 'User',
            'email': userinfo.get('email'),
            'picture': userinfo.get('picture', '')
        }
        session.permanent = True
        return redirect(url_for('workspace'))
    except Exception:
        app.logger.exception('Google sign-in failed')
        return render_template('login.html', auth_error='Google sign-in failed. Please try again.'), 400

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/app')
@login_required
def workspace():
    return render_template('index.html', google_user=session.get('google_user'))

@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({'error':'Request body must be a JSON object'}), 400
    for key in ('companyName','industry','tagline','problemStatement','solutionDescription','targetAudience','targetMarket','knownUserBase', 'monthlyPrice', 'monthlyCosts', 'customerVariableCost', 'monthlyMarketing', 'newCustomersMonthly', 'marketCustomers', 'marketPenetration'):
        if data.get(key) is not None and not isinstance(data.get(key), (str, int, float)):
            return jsonify({'error':f'{key} must be text or a number'}), 400
        data[key] = str(data.get(key) or '')[:4000]
    if data.get('knownUserBase'):
        try:
            if int(data['knownUserBase']) < 0:
                return jsonify({'error':'knownUserBase cannot be negative'}), 400
        except ValueError:
            return jsonify({'error':'knownUserBase must be a whole number'}), 400
    slides_data = generate_ai_pitch_deck(data)
    try:
        advanced_slide = build_advanced_planning_slide(data)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    if advanced_slide:
        # Keep the AI-generated deck and all existing slides intact; add one optional slide.
        slides_data.append(advanced_slide)
    
    # Save to SQLite/MySQL
    deck = PitchDeck(
        title=data.get('companyName', 'InnovateAI'),
        industry=data.get('industry', 'Tech'),
        tagline=data.get('tagline', ''),
        theme=data.get('theme', 'professional') if data.get('theme') in {'professional', 'startup', 'dark'} else 'professional',
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
        "theme": deck.theme or 'professional',
        "slides": slides_data
    })

@app.route('/api/export-pptx', methods=['POST'])
def export_pptx():
    """Generates real Microsoft PowerPoint (.pptx) file using python-pptx"""
    data = request.json or {}
    title = data.get('title', 'Pitch_Deck')
    slides_list = data.get('slides', [])
    theme = data.get('theme', 'professional')
    themes = {
        'professional': {'bg': RGBColor(248,250,252), 'heading': RGBColor(23,32,51), 'body': RGBColor(71,85,105), 'accent': RGBColor(37,99,235), 'card': RGBColor(255,255,255)},
        'startup': {'bg': RGBColor(49,46,129), 'heading': RGBColor(255,255,255), 'body': RGBColor(237,233,254), 'accent': RGBColor(196,181,253), 'card': RGBColor(67,56,202)},
        'dark': {'bg': RGBColor(9,13,22), 'heading': RGBColor(248,250,252), 'body': RGBColor(203,213,225), 'accent': RGBColor(56,189,248), 'card': RGBColor(15,23,42)}
    }
    palette = themes.get(theme, themes['professional'])

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
        fill.fore_color.rgb = palette['bg']

        # Slide Number and Category
        header_box = slide.shapes.add_textbox(Inches(1.0), Inches(0.6), Inches(11.3), Inches(0.4))
        tf_h = header_box.text_frame
        tf_h.text = f"SLIDE {idx + 1} OF {len(slides_list)} • {slide_info.get('category', 'OVERVIEW').upper()}"
        p_h = tf_h.paragraphs[0]
        p_h.font.size = Pt(11)
        p_h.font.bold = True
        p_h.font.color.rgb = palette['accent']

        # Title
        title_box = slide.shapes.add_textbox(Inches(1.0), Inches(1.0), Inches(11.3), Inches(0.8))
        tf_t = title_box.text_frame
        tf_t.word_wrap = True
        tf_t.text = slide_info.get('title', '')
        p_t = tf_t.paragraphs[0]
        p_t.font.size = Pt(28)
        p_t.font.bold = True
        p_t.font.color.rgb = palette['heading']

        # Subtitle
        if slide_info.get('subtitle'):
            sub_box = slide.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(0.5))
            tf_s = sub_box.text_frame
            tf_s.text = slide_info.get('subtitle')
            p_s = tf_s.paragraphs[0]
            p_s.font.size = Pt(14)
            p_s.font.italic = True
            p_s.font.color.rgb = palette['body']

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
                p_b.font.color.rgb = palette['body']
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
            p_val.font.color.rgb = palette['accent']

            p_lbl = tf_m.add_paragraph()
            p_lbl.text = str(m.get('label', ''))
            p_lbl.font.size = Pt(12)
            p_lbl.font.bold = True
            p_lbl.font.color.rgb = palette['heading']

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
            "theme": d.theme or 'professional',
            "created_at": d.created_at.isoformat()
        })
    return jsonify(results)

@app.route('/api/decks/<int:deck_id>/theme', methods=['PUT'])
def update_deck_theme(deck_id):
    deck = db.session.get(PitchDeck, deck_id)
    if deck is None:
        return jsonify({"error": "Deck not found"}), 404
    data = request.json or {}
    theme = data.get('theme')
    if theme not in {'professional', 'startup', 'dark'}:
        return jsonify({"error": "Invalid theme"}), 400
    deck.theme = theme
    db.session.commit()
    return jsonify({"success": True, "theme": deck.theme})

@app.route('/api/decks/<int:deck_id>', methods=['GET'])
def get_deck(deck_id):
    deck = db.session.get(PitchDeck, deck_id)
    if deck is None:
        return jsonify({"error": "Deck not found"}), 404

    slides = []
    for s in sorted(deck.slides, key=lambda item: item.order_index or 0):
        try:
            bullets = json.loads(s.bullets_json or '[]')
        except (TypeError, json.JSONDecodeError):
            bullets = []
        try:
            metrics = json.loads(s.metrics_json or '[]')
        except (TypeError, json.JSONDecodeError):
            metrics = []
        slides.append({
            "category": s.category,
            "title": s.title,
            "subtitle": s.subtitle or '',
            "bullets": bullets,
            "metrics": metrics,
            "speaker_notes": s.speaker_notes or ''
        })

    return jsonify({
        "id": deck.id,
        "title": deck.title,
        "industry": deck.industry,
        "tagline": deck.tagline or '',
        "theme": deck.theme if deck.theme in {'professional', 'startup', 'dark'} else 'professional',
        "created_at": deck.created_at.isoformat() if deck.created_at else None,
        "slides": slides
    })



@app.route('/health')
@app.route('/api/health')
def health_check():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status':'ok','database':'connected','ai_provider':'anthropic' if os.getenv('ANTHROPIC_API_KEY') else 'local-fallback'}), 200
    except Exception:
        app.logger.exception('Health check database failure')
        return jsonify({'status':'degraded','database':'unavailable'}), 503

@app.route('/api/decks/<int:deck_id>', methods=['PUT'])
def update_deck(deck_id):
    deck = db.session.get(PitchDeck, deck_id)
    if deck is None: return jsonify({'error':'Deck not found'}), 404
    data = request.get_json(silent=True) or {}
    if 'title' in data: deck.title = str(data['title'])[:120] or 'Untitled deck'
    if 'industry' in data: deck.industry = str(data['industry'])[:80]
    if 'tagline' in data: deck.tagline = str(data['tagline'])[:250]
    if 'theme' in data and data['theme'] in {'professional','startup','dark'}: deck.theme = data['theme']
    slides = data.get('slides')
    if slides is not None:
        if not isinstance(slides,list) or len(slides)>20: return jsonify({'error':'Slides must be a list of at most 20 items'}),400
        for old in list(deck.slides): db.session.delete(old)
        for idx,item in enumerate(slides):
            if not isinstance(item,dict): continue
            db.session.add(Slide(deck_id=deck.id, category=str(item.get('category','content'))[:50],
                title=str(item.get('title','Untitled'))[:200], subtitle=str(item.get('subtitle',''))[:250],
                bullets_json=json.dumps(item.get('bullets',[])[:10]), metrics_json=json.dumps(item.get('metrics',[])[:6]),
                speaker_notes=str(item.get('speaker_notes',''))[:4000], order_index=idx))
    db.session.commit()
    return jsonify({'success':True,'id':deck.id})

@app.route('/api/decks/<int:deck_id>', methods=['DELETE'])
def delete_deck(deck_id):
    deck = db.session.get(PitchDeck, deck_id)
    if deck is None: return jsonify({'error':'Deck not found'}),404
    db.session.delete(deck); db.session.commit()
    return jsonify({'success':True})

@app.route('/api/export-pdf', methods=['POST'])
def export_pdf():
    """Create a clean text-first PDF export of the submitted deck."""
    data=request.get_json(silent=True) or {}
    try:
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, ListFlowable, ListItem
        from xml.sax.saxutils import escape
        output=BytesIO()
        doc=SimpleDocTemplate(output,pagesize=landscape(A4),rightMargin=48,leftMargin=48,topMargin=42,bottomMargin=42)
        styles=getSampleStyleSheet()
        styles.add(ParagraphStyle(name='DeckTitle',parent=styles['Title'],fontSize=28,leading=34,textColor=colors.HexColor('#173253'),spaceAfter=18))
        styles.add(ParagraphStyle(name='SlideTitle',parent=styles['Heading1'],fontSize=23,leading=28,textColor=colors.HexColor('#2563eb'),spaceAfter=14))
        styles.add(ParagraphStyle(name='BodyDeck',parent=styles['BodyText'],fontSize=14,leading=20,spaceAfter=10))
        story=[]; title=escape(str(data.get('title','Pitch Deck'))[:120])
        story.extend([Paragraph(title,styles['DeckTitle']),Paragraph('Generated with AI Pitch Deck Generator',styles['BodyDeck']),PageBreak()])
        slides=data.get('slides',[])
        if not isinstance(slides,list) or not slides: return jsonify({'error':'No slides supplied'}),400
        for idx,slide in enumerate(slides[:20]):
            story.append(Paragraph(escape(str(slide.get('title','Slide'))[:200]),styles['SlideTitle']))
            if slide.get('subtitle'): story.append(Paragraph(escape(str(slide['subtitle'])[:500]),styles['BodyDeck']))
            bullets=slide.get('bullets',[])
            if isinstance(bullets,list):
                for bullet in bullets[:10]: story.append(Paragraph('• '+escape(str(bullet)[:1000]),styles['BodyDeck']))
            if slide.get('speaker_notes'):
                story.extend([Spacer(1,8),Paragraph('<b>Speaker notes</b>',styles['BodyText']),Paragraph(escape(str(slide['speaker_notes'])[:2000]),styles['BodyDeck'])])
            if idx < min(len(slides),20)-1: story.append(PageBreak())
        doc.build(story); output.seek(0)
        filename=re.sub(r'[^a-zA-Z0-9_-]+','_',str(data.get('title','pitch_deck')))[:80]+'_pitch_deck.pdf'
        return send_file(output,as_attachment=True,download_name=filename,mimetype='application/pdf')
    except Exception:
        app.logger.exception('PDF export failed')
        return jsonify({'error':'Could not create PDF. Please check slide content and try again.'}),500


if __name__ == '__main__':
    print("AI Pitch Deck Generator is starting on http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
