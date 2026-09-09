"""PostgreSQL connection helper and simple data-access functions."""
import os
import json
import psycopg2
import psycopg2.extras


def get_connection():
    """Open a new PostgreSQL connection using env vars.

    Supports either a single DATABASE_URL (what Render provides) or
    individual DB_HOST / DB_USER / DB_PASSWORD / DB_NAME / DB_PORT vars.
    """
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url)
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        dbname=os.getenv("DB_NAME", "pitchdeck_db"),
        port=int(os.getenv("DB_PORT", 5432)),
    )


def create_deck(startup_name, idea_description, industry, user_id=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO decks (user_id, startup_name, idea_description, industry, status)
           VALUES (%s, %s, %s, %s, 'draft') RETURNING id""",
        (user_id, startup_name, idea_description, industry),
    )
    deck_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return deck_id


def save_slides(deck_id, slides):
    """slides: list of dicts with keys slide_type, title, content (dict/list)."""
    conn = get_connection()
    cur = conn.cursor()
    # Replace any existing slides for this deck (regeneration case)
    cur.execute("DELETE FROM slides WHERE deck_id = %s", (deck_id,))
    for order, slide in enumerate(slides, start=1):
        cur.execute(
            """INSERT INTO slides (deck_id, slide_order, slide_type, title, content_json)
               VALUES (%s, %s, %s, %s, %s)""",
            (deck_id, order, slide["slide_type"], slide["title"], json.dumps(slide["content"])),
        )
    cur.execute("UPDATE decks SET status = 'generated' WHERE id = %s", (deck_id,))
    conn.commit()
    cur.close()
    conn.close()


def get_deck_with_slides(deck_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM decks WHERE id = %s", (deck_id,))
    deck = cur.fetchone()
    if not deck:
        cur.close()
        conn.close()
        return None
    deck = dict(deck)
    cur.execute(
        "SELECT * FROM slides WHERE deck_id = %s ORDER BY slide_order ASC", (deck_id,)
    )
    slides = [dict(row) for row in cur.fetchall()]
    for s in slides:
        content = s["content_json"]
        s["content"] = content if isinstance(content, (dict, list)) else (json.loads(content) if content else {})
        del s["content_json"]
    cur.close()
    conn.close()
    deck["slides"] = slides
    return deck


def update_slide(slide_id, title, content):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE slides SET title = %s, content_json = %s WHERE id = %s",
        (title, json.dumps(content), slide_id),
    )
    cur.execute(
        "UPDATE decks SET status = 'edited' WHERE id = (SELECT deck_id FROM slides WHERE id = %s)",
        (slide_id,),
    )
    conn.commit()
    cur.close()
    conn.close()


def mark_exported(deck_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE decks SET status = 'exported' WHERE id = %s", (deck_id,))
    conn.commit()
    cur.close()
    conn.close()
