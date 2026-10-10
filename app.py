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
