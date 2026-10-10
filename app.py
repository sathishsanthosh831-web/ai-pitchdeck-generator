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



def make_topic_illustration(slide_info, deck_title=''):
    """Render a polished, slide-specific illustration using Pillow (no paid API)."""
    from PIL import Image, ImageDraw
    import re, math
    title = str(slide_info.get('title', ''))
    subtitle = str(slide_info.get('subtitle', ''))
    bullets = ' '.join(str(x) for x in (slide_info.get('bullets') or []))
    context = f"{deck_title} {title} {subtitle} {bullets}".lower()
    category = str(slide_info.get('category', '')).lower().replace('-', '_').replace(' ', '_')
    if any(k in context for k in ('food','restaurant','delivery','meal','quickbite','cuisine')): domain='food'
    elif any(k in context for k in ('health','medical','hospital','patient','doctor','clinic')): domain='health'
    elif any(k in context for k in ('education','student','teacher','learning','course','classroom')): domain='education'
    elif any(k in context for k in ('finance','bank','payment','money','budget','investment')): domain='finance'
    elif any(k in context for k in ('environment','climate','sustain','recycle','green energy')): domain='environment'
    elif any(k in context for k in ('travel','tourism','hotel','trip','destination')): domain='travel'
    else: domain='business'
    palettes = {
      'food': ('#FFF1E8','#FF6B35','#F72585','#FFD166'), 'health': ('#E6FAF5','#0FAE9B','#2878E5','#8BE0C6'),
      'education': ('#EEF0FF','#6657E8','#A044F4','#55C3F0'), 'finance': ('#E8FFF4','#0EAD78','#246BFD','#FFD166'),
      'environment': ('#EDFFE8','#3EAA57','#087F8C','#C9F27A'), 'travel': ('#EAF7FF','#238ED0','#7558E8','#FFC857'),
      'business': ('#F0EEFF','#6554E8','#168DD4','#FFB86B')}
    bg, a, b, c = palettes[domain]
    W,H=900,620
    im=Image.new('RGB',(W,H),bg); d=ImageDraw.Draw(im)
    # soft ambient blobs and layered floating cards
    d.ellipse((590,-150,1020,280), fill='#FFFFFF')
    d.ellipse((-170,390,260,800), fill='#FFFFFF')
    d.rounded_rectangle((88,60,822,552), radius=52, fill='#D8DDF0')
    d.rounded_rectangle((70,42,804,534), radius=52, fill='#FFFFFF', outline='#FFFFFF', width=4)
    d.rounded_rectangle((88,60,786,516), radius=38, fill=bg)
    # confetti / sparkle details
    for x,y,r,col in [(145,118,9,a),(733,128,12,b),(710,445,8,c),(176,455,7,b),(665,92,5,a)]:
        d.ellipse((x-r,y-r,x+r,y+r),fill=col)
    def card(box, fill='#FFFFFF', outline=None, radius=22, width=3):
        d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width if outline else 1)
    def check(cx,cy,col=a):
        d.ellipse((cx-22,cy-22,cx+22,cy+22),fill=col)
        d.line((cx-11,cy,cx-2,cy+9,cx+13,cy-11),fill='white',width=7)
    if category=='title':
        # premium cover: luminous deck screen, stacked cards, idea bulb
        d.ellipse((440,105,720,385),fill='#D8D5FF')
        card((350,130,690,380),'#172554',None,30)
        card((370,150,670,352),'#FFFFFF',None,20)
        d.rounded_rectangle((395,175,520,192),radius=8,fill=a)
        d.rounded_rectangle((395,207,625,221),radius=7,fill='#DDE5F5')
        d.rounded_rectangle((395,235,595,249),radius=7,fill='#DDE5F5')
        card((400,272,492,326), '#EDE9FE',None,14); card((505,272,635,326),'#E0F2FE',None,14)
        d.line((420,308,440,290,458,300,475,283),fill=a,width=7)
        d.ellipse((570,70,650,150),fill=c); d.rounded_rectangle((594,137,626,166),radius=8,fill='#F59E0B')
        d.arc((585,65,635,125),180,360,fill='white',width=5)
        # floating mini presentation cards
        card((245,215,350,320),'#FFFFFF',None,18); d.rectangle((265,237,330,245),fill=b); d.line((265,265,326,265),fill='#CBD5E1',width=5); d.line((265,281,315,281),fill='#CBD5E1',width=5)
        card((615,390,730,458),'#FFFFFF',None,16); d.line((637,433,660,415,680,426,708,401),fill=a,width=6)
    elif category=='problem':
        # overwhelmed creator, scattered task cards, visual stress cues
        card((155,140,360,410),'#FFFFFF',a,30,5); d.ellipse((210,178,305,273),fill='#FFD8C8')
        d.arc((232,222,285,260),200,340,fill='#9F3B58',width=6); d.ellipse((232,210,242,220),fill='#26324B'); d.ellipse((275,210,285,220),fill='#26324B')
        d.rounded_rectangle((195,285,320,385),radius=35,fill=b); d.line((225,315,290,315),fill='white',width=7); d.line((225,340,285,340),fill='white',width=7)
        card((420,125,680,205),'#FFFFFF',None,20); d.ellipse((444,151,470,177),fill='#FB7185'); d.line((451,158,463,170),fill='white',width=4); d.line((463,158,451,170),fill='white',width=4); d.line((490,157,640,157),fill='#CBD5E1',width=8); d.line((490,179,610,179),fill='#E2E8F0',width=7)
        card((450,230,690,310),'#FFFFFF',None,20); d.ellipse((474,256,500,282),fill=c); d.line((520,262,650,262),fill='#CBD5E1',width=8); d.line((520,284,620,284),fill='#E2E8F0',width=7)
        card((420,335,670,415),'#FFFFFF',None,20); d.ellipse((444,361,470,387),fill=a); d.line((490,367,635,367),fill='#CBD5E1',width=8); d.line((490,389,600,389),fill='#E2E8F0',width=7)
        for x,y in [(390,105),(690,335),(385,440)]: d.line((x-12,y,x+12,y),fill=b,width=5); d.line((x,y-12,x,y+12),fill=b,width=5)
    elif category=='solution':
        # phone showing a generated deck, magic sparkles, export cards
        d.ellipse((230,110,665,470),fill='#D8F4FF')
        card((335,95,555,435),'#182448',None,34); card((350,112,540,415),'#FFFFFF',None,25)
        d.rounded_rectangle((375,140,515,157),radius=8,fill=a); d.rounded_rectangle((375,178,510,188),radius=5,fill='#D9E2F2')
        card((372,210,518,292),'#F1EEFF',None,15); d.line((390,270,420,245,447,257,485,226),fill=b,width=7)
        d.rounded_rectangle((375,312,510,329),radius=7,fill='#D9E2F2'); d.rounded_rectangle((375,342,480,359),radius=7,fill='#D9E2F2')
        card((565,170,710,255),'#FFFFFF',None,18); d.rounded_rectangle((590,193,685,207),radius=6,fill=a); d.rounded_rectangle((590,220,660,233),radius=6,fill='#CBD5E1')
        card((195,325,335,405),'#FFFFFF',None,18); d.ellipse((220,345,270,395),fill=c); d.line((235,370,245,380,260,357),fill='white',width=5)
        for x,y in [(260,125),(680,120),(640,390)]: d.line((x-13,y,x+13,y),fill=c,width=5); d.line((x,y-13,x,y+13),fill=c,width=5)
    elif category=='features':
        # six feature tiles with distinct pictograms
        tiles=[(145,125,a,'AI'),(360,125,b,'IMG'),(575,125,c,'THEME'),(145,305,b,'PPT'),(360,305,c,'EDIT'),(575,305,a,'PDF')]
        for x,y,col,label in tiles:
            card((x,y,x+170,y+135),'#FFFFFF',None,22)
            d.ellipse((x+18,y+18,x+67,y+67),fill=col)
            if label=='AI': d.line((x+31,y+42,x+42,y+29,x+54,y+42,x+42,y+54,x+31,y+42),fill='white',width=3)
            elif label=='IMG': d.rectangle((x+29,y+29,x+56,y+54),outline='white',width=3); d.ellipse((x+34,y+33,x+42,y+41),fill='white'); d.line((x+30,y+51,x+40,y+43,x+47,y+49,x+55,y+40),fill='white',width=3)
            elif label=='THEME': d.ellipse((x+30,y+30,x+55,y+55),outline='white',width=4); d.ellipse((x+39,y+35,x+45,y+41),fill='white')
            elif label=='PPT': d.rectangle((x+31,y+28,x+54,y+56),outline='white',width=3); d.line((x+36,y+36,x+49,y+36),fill='white',width=3)
            elif label=='EDIT': d.line((x+30,y+51,x+50,y+31),fill='white',width=5); d.line((x+31,y+55,x+40,y+54),fill='white',width=3)
            else: d.arc((x+29,y+29,x+56,y+56),30,320,fill='white',width=4)
            d.rounded_rectangle((x+18,y+83,x+148,y+92),radius=5,fill='#CBD5E1'); d.rounded_rectangle((x+18,y+104,x+120,y+112),radius=5,fill='#E2E8F0')
    elif category=='audience':
        # diverse user group with individual cards
        people=[(240,205,a),(390,175,b),(540,205,c)]
        for x,y,col in people:
            d.ellipse((x-44,y-44,x+44,y+44),fill='#FFDCCB')
            d.arc((x-48,y-48,x+48,y+45),180,360,fill=col,width=17)
            d.rounded_rectangle((x-65,y+47,x+65,y+180),radius=35,fill=col)
            d.ellipse((x-16,y-5,x-7,y+4),fill='#25304A'); d.ellipse((x+8,y-5,x+17,y+4),fill='#25304A'); d.arc((x-15,y+5,x+15,y+27),10,170,fill='#9F3B58',width=4)
        card((180,420,630,475),'#FFFFFF',None,20); d.rounded_rectangle((215,440,320,451),radius=5,fill=a); d.rounded_rectangle((350,440,455,451),radius=5,fill=b); d.rounded_rectangle((485,440,590,451),radius=5,fill=c)
    elif category=='workflow':
        # diagonal connected process nodes and central app panel
        steps=[(145,150,a),(350,235,b),(555,150,c),(555,355,a)]
        for i,(x,y,col) in enumerate(steps):
            card((x,y,x+150,y+110),'#FFFFFF',col,24,4)
            d.ellipse((x+47,y+16,x+103,y+72),fill=col)
            if i==0: d.rounded_rectangle((x+62,y+32,x+88,y+54),radius=5,outline='white',width=4)
            elif i==1: d.line((x+61,y+45,x+73,y+56,x+91,y+32),fill='white',width=5)
            elif i==2: d.line((x+63,y+54,x+87,y+30),fill='white',width=5); d.line((x+66,y+32,x+87,y+32),fill='white',width=4)
            else: d.line((x+75,y+30,x+75,y+53),fill='white',width=5); d.polygon([(x+61,y+45),(x+89,y+45),(x+75,y+61)],fill='white')
            d.rounded_rectangle((x+28,y+83,x+122,y+91),radius=4,fill='#CBD5E1')
        d.line((295,205,350,270),fill=a,width=8); d.polygon([(350,270),(330,263),(341,250)],fill=a)
        d.line((500,270,555,205),fill=b,width=8); d.polygon([(555,205),(537,216),(549,225)],fill=b)
        d.line((630,260,630,355),fill=c,width=8); d.polygon([(630,355),(619,338),(641,338)],fill=c)
    elif category=='business_model':
        # revenue stream tiles, coin stack and upward path
        card((145,135,340,390),'#FFFFFF',None,28); card((360,135,555,390),'#FFFFFF',None,28); card((575,135,750,390),'#FFFFFF',None,28)
        for x,col in [(240,a),(455,b),(660,c)]:
            d.ellipse((x-42,170,x+42,254),fill=col)
        d.text((222,191),'$',fill='white',stroke_width=2,stroke_fill='white'); d.rectangle((433,193,477,230),outline='white',width=5); d.line((440,203,470,203),fill='white',width=4); d.line((440,215,463,215),fill='white',width=4)
        d.ellipse((640,190,680,230),outline='white',width=5); d.ellipse((651,201,669,219),outline='white',width=4)
        for x,y in [(195,300),(215,285),(235,300),(255,285),(275,300)]: d.ellipse((x,y,x+32,y+32),fill='#FFD166',outline='#E5A62B',width=2)
        d.line((395,320,440,285,480,300,520,250),fill=a,width=9); d.polygon([(520,250),(497,257),(514,273)],fill=a)
        d.line((600,320,640,285,675,295,715,240),fill=b,width=9); d.polygon([(715,240),(693,248),(709,263)],fill=b)
        for x in [180,395,610]: d.rounded_rectangle((x,345,x+120,357),radius=6,fill='#DCE4F1')
    elif category in ('future','roadmap','conclusion'):
        # cinematic future horizon with layered mountains and a luminous path
        d.rectangle((100,340,770,500),fill='#172554')
        d.polygon([(100,390),(250,260),(360,385),(480,245),(630,390),(770,280),(770,500),(100,500)],fill='#6D5CE8')
        d.polygon([(100,430),(280,330),(420,430),(570,320),(770,430),(770,500),(100,500)],fill='#263C8C')
        d.ellipse((540,115,680,255),fill='#FFD166'); d.ellipse((568,143,652,227),fill='#FFF0B3')
        d.line((350,500,420,445,455,395,510,365,550,315),fill='#FDE68A',width=22); d.line((350,500,420,445,455,395,510,365,550,315),fill='white',width=4)
        # futuristic skyline
        for x,y,w,h in [(590,290,35,100),(632,260,42,130),(680,300,28,90),(715,275,32,115)]: d.rectangle((x,y,x+w,y+h),fill='#101C4A')
        for x,y in [(600,310),(600,335),(642,285),(642,310),(690,320),(724,295)]: d.rectangle((x,y,x+7,y+8),fill='#FFD166')
        d.ellipse((165,145,205,185),fill=a); d.line((185,125,185,105),fill=a,width=5); d.line((145,165,125,165),fill=a,width=5); d.line((225,165,245,165),fill=a,width=5)
    else:
        # elegant generic topic illustration: dashboard + analytics + check
        card((165,125,700,420),'#FFFFFF',None,28)
        d.rounded_rectangle((195,155,665,198),radius=14,fill='#F1F5F9'); d.ellipse((211,170,224,183),fill=a); d.ellipse((233,170,246,183),fill=b); d.ellipse((255,170,268,183),fill=c)
        for x,y,col in [(205,230,a),(350,230,b),(495,230,c)]:
            card((x,y,x+125,y+145),bg,None,18); d.ellipse((x+38,y+18,x+87,y+67),fill=col); d.rounded_rectangle((x+20,y+86,x+105,y+95),radius=5,fill='#CBD5E1'); d.rounded_rectangle((x+20,y+105,x+88,y+114),radius=5,fill='#E2E8F0')
        d.line((220,390,320,355,420,370,560,300),fill=a,width=9); d.polygon([(560,300),(537,306),(551,325)],fill=a)
    # subtle footer label strip, kept visually secondary to the illustration
    d.rounded_rectangle((120,470,760,502),radius=14,fill='#FFFFFF')
    label = re.sub(r'[^A-Za-z0-9 &-]', '', title).strip()[:58] or domain.title()
    try: d.text((145,479), label, fill='#24304A', stroke_width=0)
    except Exception: pass
    out=BytesIO(); im.save(out, format='PNG', optimize=True); out.seek(0); return out

# ----------------- PITCHORA PRESENTATION GENERATOR LOGIC -----------------
def generate_ai_pitch_deck(data):
    """Build an expanded, topic-aware pitch deck from the submitted idea.

    This uses transparent rule-based generation (no external AI API). It expands
    the inputs into presentation sections and labels suggestions as proposals.
    It deliberately avoids unsupported market statistics or claimed results.
    """
    import re

    def clean(value, fallback, limit=1800):
        value = re.sub(r"\s+", " ", str(value or "")).strip()
        return value[:limit] if value else fallback

    company = clean(data.get("companyName"), "My Project", 120)
    industry = clean(data.get("industry"), "General", 120)
    tagline = clean(data.get("tagline"), "A practical idea designed around a real user need.", 250)
    problem = clean(data.get("problemStatement"), "Users face a challenge that could be addressed more conveniently.")
    solution = clean(data.get("solutionDescription"), "A proposed service designed to address the stated challenge.")
    target = clean(data.get("targetAudience"), "People who experience the stated problem.", 250)
    context = (company + " " + industry + " " + tagline + " " + problem + " " + solution).lower()

    def split_points(text, limit=4):
        pieces = [re.sub(r"^[\s•*\-]+", "", p).strip() for p in re.split(r"(?<=[.!?])\s+|\n+", text)]
        return [p for p in pieces if p][:limit] or [text]

    problems = split_points(problem)
    solutions = split_points(solution)
    p0, s0 = problems[0], solutions[0]

    if any(k in context for k in ["food", "restaurant", "delivery", "quickbite", "meal"]):
        feature_points = [
            "Restaurant discovery and menu browsing in one place",
            "Order placement with a clear order summary",
            "Order-status updates so customers know what is happening",
            "Secure payment options and digital receipts",
            "Ratings and feedback to help users make informed choices",
        ]
        opportunity_points = [
            "Offer filters for cuisine, price, dietary needs, and delivery time",
            "Provide restaurants with order and customer-feedback summaries",
            "Explore loyalty rewards and personalized meal suggestions",
        ]
        revenue_points = [
            "Restaurant commission on completed orders (proposed)",
            "Delivery fees shown clearly before checkout (proposed)",
            "Optional restaurant promotions or customer membership (future options)",
        ]
        audience_points = [
            "Customers who want convenient access to nearby food options",
            "Local restaurants seeking an additional online ordering channel",
            "Delivery partners who fulfil orders in supported areas",
        ]
        differentiators = [
            "A simple flow from restaurant discovery to order tracking",
            "Clear order information and transparent charges",
            "Feedback that can guide service improvements",
        ]
    elif any(k in context for k in ["health", "medical", "hospital", "patient", "medicare"]):
        feature_points = [
            "A clear interface for entering or viewing relevant information",
            "Organized records that are easier to review",
            "Helpful reminders or status updates where appropriate",
            "Privacy-aware access to user information",
            "A clear route to qualified professional support when needed",
        ]
        opportunity_points = [
            "Test the workflow with intended users and qualified domain reviewers",
            "Improve accessibility and support for different user needs",
            "Explore secure integrations only after privacy and compliance review",
        ]
        revenue_points = ["Institution or service subscription (possible option)", "Paid administrative tools (possible option)", "Partnerships with suitable providers (subject to review)"]
        audience_points = [f"Primary users: {target}", "Healthcare staff or service providers involved in the workflow", "Administrators responsible for service operations"]
        differentiators = ["A focused workflow for the stated user need", "Information presented in a clear and organized way", "Designed to complement—not replace—professional judgement"]
    elif any(k in context for k in ["education", "student", "learning", "school", "edtech", "tutor"]):
        feature_points = ["Learning materials grouped by topic", "Step-by-step explanations for difficult concepts", "Practice questions with feedback", "Progress indicators to help learners identify gaps", "Accessible use across common devices"]
        opportunity_points = ["Add learning paths for different skill levels", "Use learner feedback to improve explanations", "Explore teacher or mentor dashboards as a future feature"]
        revenue_points = ["Free basic learning tools with optional premium features", "Institution subscriptions (possible option)", "Paid learning resources (possible option)"]
        audience_points = [f"Primary learners: {target}", "Teachers, mentors, or trainers who support learning", "Institutions looking for supplementary learning tools"]
        differentiators = ["Beginner-friendly explanations", "Practice linked to learning goals", "A feedback loop for continuous improvement"]
    elif any(k in context for k in ["environment", "eco", "energy", "climate", "logistics", "route", "transport"]):
        feature_points = ["Capture the information needed for planning", "Compare possible routes or operating choices", "Present recommendations with understandable reasons", "Track progress against selected operational goals", "Review outcomes and adjust plans over time"]
        opportunity_points = ["Test recommendations against real operating conditions", "Add useful reporting and trend summaries", "Explore integrations after validating data quality"]
        revenue_points = ["Subscription for business users (possible option)", "Tiered plans based on usage (possible option)", "Setup or support services (possible option)"]
        audience_points = [f"Primary users: {target}", "Operations teams responsible for daily planning", "Organizations seeking more efficient processes"]
        differentiators = ["A workflow focused on a specific operational problem", "Recommendations that users can review before acting", "Improvements guided by observed results"]
    else:
        feature_points = [
            "A straightforward way to enter or access the required information",
            "A clear view of the main task or service",
            "Useful status updates and feedback",
            "Organized records to support follow-up",
            "A simple interface designed for the intended users",
        ]
        opportunity_points = [
            "Validate the concept with a small group of intended users",
            "Prioritize features based on user feedback",
            "Explore automation or integrations only where they solve a real need",
        ]
        revenue_points = ["Subscription or service fee (possible option)", "Optional premium functionality (possible option)", "Suitable partnerships (possible option)"]
        audience_points = [f"Primary users: {target}", "Organizations that experience the stated problem", "People who support or manage the related workflow"]
        differentiators = ["A focused response to the stated problem", "A simple experience for the intended audience", "Room to improve based on real user feedback"]

    problem_impacts = [
        f"User challenge: {p0}",
        f"Why it matters: it can make the related task harder or less convenient for {target.lower()}.",
        "Opportunity: make the process clearer, easier to access, and simpler to follow.",
    ]
    solution_steps = [
        f"Core proposal: {s0}",
        f"User journey: help {target.lower()} move from the initial need to the intended outcome.",
        "Design principle: keep the main steps understandable and provide clear feedback.",
    ]
    roadmap = [
        "Phase 1 — Confirm the user problem and collect feedback from the target audience.",
        "Phase 2 — Build a small working version with the essential workflow.",
        "Phase 3 — Test usability, reliability, and the quality of the results.",
        "Phase 4 — Prioritize improvements using feedback and observed evidence.",
    ]
    value_points = [
        "Convenience: aim to reduce unnecessary effort in the current process.",
        "Clarity: present the information users need at the right step.",
        "Continuous improvement: use feedback to decide what to improve next.",
    ]

    def slide(category, title, subtitle, bullets, metrics, notes):
        return {"category": category, "title": title, "subtitle": subtitle,
                "bullets": bullets, "metrics": metrics, "speaker_notes": notes}

    return [
        slide("title", company, tagline,
              [f"Industry: {industry}", f"Designed for: {target}"],
              [{"label": "Project Area", "value": industry[:24]}, {"label": "Pitch Focus", "value": "User Need"}],
              f"Introduce {company}. Explain the user need behind the idea, the proposed approach, and who may benefit. This presentation describes a proposal, not verified business results."),
        slide("problem", "The Problem", "The user need behind this idea", problem_impacts,
              [{"label": "Focus", "value": "User Need"}],
              f"Start with the challenge: {problem} Explain how this may affect the intended users, without claiming impact figures that have not been measured."),
        slide("solution", "The Proposed Solution", "How the idea could address the challenge", solution_steps,
              [{"label": "Approach", "value": "Proposed"}],
              f"Describe the proposed approach: {solution} Explain how the intended users would interact with it."),
        slide("features", "Key Features", "Core capabilities to consider for the first version", feature_points,
              [{"label": "Priority", "value": "Core Workflow"}],
              "These are suggested features based on the project topic. Only describe them as completed features if they have actually been implemented."),
        slide("audience", "Target Audience", "Who may use or benefit from the project", audience_points,
              [{"label": "Audience", "value": "User Groups"}],
              f"The entered target audience is {target}. These groups are suggested stakeholders; validate them during project research."),
        slide("workflow", "How It Could Work", "A simple user journey", [
            "1. Discover or enter the information related to the user's need.",
            "2. Review the available details and choose the relevant action.",
            "3. Receive a clear result, confirmation, or next step.",
            "4. Share feedback that can guide future improvements.",
        ], [{"label": "Journey", "value": "4 Steps"}],
             "Walk through the proposed user journey. Adjust these steps to match the actual functions implemented in the project."),
        slide("business_model", "Possible Business Model", "Options to evaluate if the project becomes a service", revenue_points,
              [{"label": "Status", "value": "Options"}],
              "These are possible revenue approaches, not claims about current revenue. Choose only the model that suits the project and validate its feasibility."),
        slide("future", "Future Scope & Conclusion", "Next steps and the main takeaway", [
            "Begin with the essential features and test them with intended users.",
            "Improve reliability, usability, and accessibility using feedback.",
            "Add advanced features only when they solve a demonstrated need.",
            f"Takeaway: {company} proposes a response to the problem of {p0[0].lower() + p0[1:] if p0 else problem}",
        ], [{"label": "Next Action", "value": "Build & Test"}],
             f"Conclude by summarizing the need ({problem}), the proposal ({solution}), and the intended users ({target}). Future features should depend on user feedback and testing."),
    ]

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
        p_t.font.size = Pt(38 if idx == 0 else 28)
        p_t.font.bold = True
        p_t.font.name = 'Aptos Display' if idx == 0 else 'Aptos'
        p_t.font.color.rgb = palette['accent'] if idx == 0 else palette['heading']
        if idx == 0:
            # A short accent rule gives the cover title a polished, branded finish.
            rule = slide.shapes.add_shape(1, Inches(1.0), Inches(1.92), Inches(1.65), Inches(0.07))
            rule.fill.solid()
            rule.fill.fore_color.rgb = palette['accent']
            rule.line.fill.background()

        # Subtitle
        if slide_info.get('subtitle'):
            sub_box = slide.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(0.5))
            tf_s = sub_box.text_frame
            tf_s.text = slide_info.get('subtitle')
            p_s = tf_s.paragraphs[0]
            p_s.font.size = Pt(14)
            p_s.font.italic = True
            p_s.font.color.rgb = palette['body']

        # Actual topic-aware illustration, generated from the submitted topic and slide text.
        try:
            illustration = make_topic_illustration(slide_info, title)
            slide.shapes.add_picture(illustration, Inches(9.15), Inches(2.55), width=Inches(3.35), height=Inches(2.5))
        except Exception:
            app.logger.exception('Could not create slide illustration')

        # Bullet Points
        bullets = slide_info.get('bullets', [])
        if bullets:
            content_box = slide.shapes.add_textbox(Inches(1.0), Inches(2.5), Inches(7.7), Inches(4.2))
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

        credit_box = slide.shapes.add_textbox(Inches(10.1), Inches(7.12), Inches(2.2), Inches(0.18))
        credit_tf = credit_box.text_frame
        credit_tf.text = "Created by Seema Anjum"
        credit_tf.paragraphs[0].alignment = PP_ALIGN.RIGHT
        credit_tf.paragraphs[0].font.size = Pt(7)
        credit_tf.paragraphs[0].font.color.rgb = palette['body']

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


@app.route('/api/export-pdf', methods=['POST'])
def export_pdf():
    """Create a PDF copy of the current pitch deck using a simple, robust canvas layout."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import landscape, letter
        from reportlab.lib import colors
        from reportlab.pdfbase.pdfmetrics import stringWidth
        import textwrap

        data = request.get_json(silent=True) or {}
        title = str(data.get('title') or 'Pitch Deck')[:180]
        slides_list = data.get('slides') or []
        theme = str(data.get('theme') or 'professional')
        if not isinstance(slides_list, list) or not slides_list:
            return jsonify({'error': 'Generate a pitch deck before exporting to PDF.'}), 400

        page_w, page_h = landscape(letter)
        palettes = {
            'professional': ('#172033', '#475569', '#2563eb', '#eff6ff'),
            'startup': ('#312e81', '#3730a3', '#7c3aed', '#f5f3ff'),
            'dark': ('#111827', '#374151', '#0284c7', '#eff6ff'),
        }
        heading_hex, body_hex, accent_hex, background_hex = palettes.get(theme, palettes['professional'])
        output = BytesIO()
        pdf = canvas.Canvas(output, pagesize=(page_w, page_h), pageCompression=1)
        pdf.setTitle(title)
        pdf.setAuthor('Pitchora — Intelligent Pitch Deck Creator for Business Ideas')

        def safe_text(value):
            # PDF built-in fonts cannot render every Unicode glyph; replace problematic symbols safely.
            value = str(value if value is not None else '')
            replacements = {'’': "'", '‘': "'", '“': '"', '”': '"', '–': '-', '—': '-', '•': '-', '…': '...'}
            for old, new_value in replacements.items():
                value = value.replace(old, new_value)
            return value.encode('latin-1', 'replace').decode('latin-1')

        def wrap_text(value, font_name, font_size, max_width):
            value = safe_text(value).replace('\r', ' ').replace('\n', ' ')
            words = value.split()
            lines, current = [], ''
            for word in words:
                candidate = word if not current else current + ' ' + word
                if stringWidth(candidate, font_name, font_size) <= max_width:
                    current = candidate
                else:
                    if current:
                        lines.append(current)
                    current = word
            if current:
                lines.append(current)
            return lines or ['']

        def draw_wrapped(value, x, y, max_width, font_name='Helvetica', font_size=15, leading=21, color=body_hex, max_lines=8):
            pdf.setFont(font_name, font_size)
            pdf.setFillColor(colors.HexColor(color))
            lines = wrap_text(value, font_name, font_size, max_width)[:max_lines]
            for line in lines:
                pdf.drawString(x, y, line)
                y -= leading
            return y

        # Cover page
        pdf.setFillColor(colors.HexColor(background_hex))
        pdf.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        pdf.setFillColor(colors.HexColor(accent_hex))
        pdf.rect(0, 0, 14, page_h, fill=1, stroke=0)
        y = page_h - 130
        y = draw_wrapped(title, 62, y, page_w - 124, 'Helvetica-Bold', 30, 38, heading_hex, 3)
        y -= 14
        draw_wrapped('PITCH DECK', 64, y, page_w - 128, 'Helvetica-Bold', 12, 18, accent_hex, 1)
        y -= 40
        draw_wrapped(f'{len(slides_list)} slides', 64, y, page_w - 128, 'Helvetica', 16, 22, body_hex, 1)
        pdf.setStrokeColor(colors.HexColor(accent_hex))
        pdf.setLineWidth(1.5)
        pdf.line(64, 54, page_w - 64, 54)
        pdf.setFont('Helvetica', 9)
        pdf.setFillColor(colors.HexColor(body_hex))
        pdf.drawString(64, 36, 'Created with Pitchora — Turning Business Ideas into Professional Presentations')
        pdf.showPage()

        for idx, slide in enumerate(slides_list):
            if not isinstance(slide, dict):
                slide = {'title': f'Slide {idx + 1}', 'bullets': [str(slide)]}
            pdf.setFillColor(colors.white)
            pdf.rect(0, 0, page_w, page_h, fill=1, stroke=0)
            pdf.setFillColor(colors.HexColor(accent_hex))
            pdf.rect(0, page_h - 12, page_w, 12, fill=1, stroke=0)
            pdf.setFont('Helvetica-Bold', 9)
            pdf.setFillColor(colors.HexColor(accent_hex))
            category = safe_text(slide.get('category') or 'OVERVIEW').upper()
            pdf.drawString(48, page_h - 42, f'SLIDE {idx + 1} OF {len(slides_list)}  |  {category[:70]}')
            y = page_h - 82
            y = draw_wrapped(slide.get('title') or f'Slide {idx + 1}', 48, y, page_w - 96, 'Helvetica-Bold', 24, 29, heading_hex, 2)
            subtitle = str(slide.get('subtitle') or '').strip()
            if subtitle:
                y -= 6
                y = draw_wrapped(subtitle, 50, y, page_w - 100, 'Helvetica-Oblique', 12, 17, accent_hex, 2)
            # Topic-aware illustration also appears in the PDF export.
            try:
                from reportlab.lib.utils import ImageReader
                image_bytes = make_topic_illustration(slide, title)
                pdf.drawImage(ImageReader(image_bytes), page_w - 250, page_h - 340, width=190, height=140, preserveAspectRatio=True, mask='auto')
            except Exception:
                app.logger.exception('Could not add PDF slide illustration')
            y -= 18
            bullets = slide.get('bullets') or []
            if isinstance(bullets, str):
                bullets = [bullets]
            if not isinstance(bullets, (list, tuple)):
                bullets = [str(bullets)]
            for bullet in bullets[:10]:
                if y < 105:
                    break
                lines = wrap_text(bullet, 'Helvetica', 14, page_w - 135)
                pdf.setFillColor(colors.HexColor(accent_hex))
                pdf.circle(59, y + 4, 3, fill=1, stroke=0)
                y = draw_wrapped(bullet, 72, y, page_w - 120, 'Helvetica', 14, 20, body_hex, 3) - 9
            metrics = slide.get('metrics') or []
            if isinstance(metrics, list):
                for metric in metrics[:4]:
                    if y < 90 or not isinstance(metric, dict):
                        continue
                    line = f"{metric.get('value', '')}  {metric.get('label', '')}"
                    y = draw_wrapped(line, 52, y, page_w - 104, 'Helvetica-Bold', 12, 17, accent_hex, 1) - 5
            notes = str(slide.get('speaker_notes') or '').strip()
            if notes and y > 90:
                y -= 5
                draw_wrapped('Speaker notes: ' + notes, 50, y, page_w - 100, 'Helvetica-Oblique', 9, 12, body_hex, 3)
            pdf.setStrokeColor(colors.HexColor(accent_hex))
            pdf.setLineWidth(0.8)
            pdf.line(48, 42, page_w - 48, 42)
            pdf.setFont('Helvetica', 8)
            pdf.setFillColor(colors.HexColor(body_hex))
            pdf.drawString(48, 27, safe_text(title)[:90])
            pdf.drawRightString(page_w - 48, 27, f'Page {idx + 2}')
            pdf.showPage()

        pdf.save()
        output.seek(0)
        filename = ''.join(ch if ch.isalnum() or ch in '-_' else '_' for ch in title).strip('_').lower() or 'pitch_deck'
        return send_file(output, as_attachment=True, download_name=f'{filename}_pitch_deck.pdf', mimetype='application/pdf')
    except Exception as exc:
        app.logger.exception('PDF export failed')
        return jsonify({'error': f'PDF export failed: {type(exc).__name__}: {str(exc)[:240]}'}), 500


@app.route('/api/slide-illustration', methods=['POST'])
def slide_illustration():
    data = request.get_json(silent=True) or {}
    slide = data.get('slide') or {}
    title = str(data.get('deck_title') or '')
    image_bytes = make_topic_illustration(slide, title)
    return send_file(image_bytes, mimetype='image/png', download_name='pitchora-slide-illustration.png')

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

if __name__ == '__main__':
    print("Pitchora is starting on http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
