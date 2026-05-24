from __future__ import annotations

import html
import math
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import reportlab.rl_config
from loguru import logger as log
from PIL import Image as PILImage
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image as RLImage
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import selectinload
from sqlmodel import select

from config import IMAGE_DIR
from util.models import (
    Game,
    RelatedGame,
)

reportlab.rl_config.useA85 = 0

if TYPE_CHECKING:
    import io

    from reportlab.pdfgen.canvas import Canvas
    from reportlab.platypus import (
        Flowable,
    )
    from sqlmodel import Session


def normalize_special_chars(text: str) -> str:
    """Normalize common cp1252 special characters to latin-1 equivalents to prevent rendering issues."""
    replacements = {
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u2018": "'",  # left single quote
        "\u2019": "'",  # right single quote
        "\u201a": "'",  # single low-9 quote
        "\u201c": '"',  # left double quote
        "\u201d": '"',  # right double quote
        "\u201e": '"',  # double low-9 quote
        "\u2026": "...",  # ellipsis
        "\u2122": "(TM)",  # trademark
        "\u0152": "OE",  # ligature OE
        "\u0153": "oe",  # ligature oe
        "\u0160": "S",  # S with caron
        "\u0161": "s",  # s with caron
        "\u017d": "Z",  # Z with caron
        "\u017e": "z",  # z with caron
        "\u0192": "f",  # florin
        "\u2022": "*",  # bullet
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    return text


def safe_xml_text(text: str | None) -> str:
    """Safely escape text for ReportLab Paragraph XML parsing and ensure latin-1 compatibility."""
    if not text:
        return ""

    # Unescape first to resolve any existing HTML entities, then escape for XML
    unencoded = html.unescape(text)

    # Normalize special characters to prevent square/tofu rendering
    normalized = normalize_special_chars(unencoded)

    # Replace non-latin-1 characters with "?" to prevent square/tofu rendering in PDF
    clean_text = normalized.encode("latin-1", errors="replace").decode(
        "latin-1"
    )

    escaped = html.escape(clean_text)
    # Replace newlines with break tags
    return escaped.replace("\n", "<br/>")


def get_scaled_image(
    img_path: Path, max_width: float, max_height: float
) -> RLImage | None:
    """Scale a PIL image proportionally and wrap in ReportLab Image flowable."""
    try:
        if not img_path.exists() or not img_path.is_file():
            return None
        with PILImage.open(img_path) as img:
            w, h = img.size

        aspect = w / h
        if w > h:
            new_w = min(w, max_width)
            new_h = new_w / aspect
            if new_h > max_height:
                new_h = max_height
                new_w = new_h * aspect
        else:
            new_h = min(h, max_height)
            new_w = new_h * aspect
            if new_w > max_width:
                new_w = max_width
                new_h = new_w / aspect
        return RLImage(str(img_path), width=new_w, height=new_h)
    except Exception as e:
        log.warning(f"Error scaling cover image {img_path}: {e}")
        return None


def get_image_fallback(width: float, height: float) -> Table:
    """Return a styled ReportLab Table to serve as a fallback image box."""
    style_fallback = ParagraphStyle(
        "FallbackTextStyle",
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        alignment=1,  # Center
        textColor=colors.HexColor("#64748b"),
    )
    fallback_text = Paragraph("No Image<br/>Available", style_fallback)
    t = Table([[fallback_text]], colWidths=[width], rowHeights=[height])
    t.setStyle(
        TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ])
    )
    return t


def make_metadata_table(game: Game, style_body: ParagraphStyle) -> Table:
    """Create a formatted key-value table for game details."""
    players = f"{game.min_players}"
    if game.max_players and game.max_players != game.min_players:
        players += f" – {game.max_players}"
    players += " players"

    play_time = f"{game.min_play_time}"
    if game.max_play_time and game.max_play_time != game.min_play_time:
        play_time += f" – {game.max_play_time}"
    play_time += " mins"

    complexity = (
        f"{game.complexity:.2f} / 5.0"
        if game.complexity is not None
        else "N/A"
    )
    rating = (
        f"{game.bgg_rating:.1f} / 10.0"
        if game.bgg_rating is not None
        else "N/A"
    )

    pub_list = [safe_xml_text(p.name) for p in game.publishers]
    if len(pub_list) > 3:
        publishers = ", ".join(pub_list[:3]) + f" (+{len(pub_list) - 3} more)"
    else:
        publishers = ", ".join(pub_list) or "N/A"

    des_list = [safe_xml_text(a.name) for a in game.authors]
    if len(des_list) > 3:
        designers = ", ".join(des_list[:3]) + f" (+{len(des_list) - 3} more)"
    else:
        designers = ", ".join(des_list) or "N/A"

    data = [
        [
            Paragraph("<b>Released:</b>", style_body),
            Paragraph(str(game.release_year or "N/A"), style_body),
        ],
        [
            Paragraph("<b>Players:</b>", style_body),
            Paragraph(players, style_body),
        ],
        [
            Paragraph("<b>Play Time:</b>", style_body),
            Paragraph(play_time, style_body),
        ],
        [
            Paragraph("<b>Age:</b>", style_body),
            Paragraph(
                f"{game.min_age}+" if game.min_age else "N/A", style_body
            ),
        ],
        [
            Paragraph("<b>Complexity:</b>", style_body),
            Paragraph(complexity, style_body),
        ],
        [
            Paragraph("<b>BGG Rating:</b>", style_body),
            Paragraph(rating, style_body),
        ],
        [
            Paragraph("<b>Designer:</b>", style_body),
            Paragraph(designers, style_body),
        ],
        [
            Paragraph("<b>Publisher:</b>", style_body),
            Paragraph(publishers, style_body),
        ],
    ]
    t = Table(data, colWidths=[80, 254])
    t.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ])
    )
    return t


def draw_later_page_footer(canvas: Canvas, doc: SimpleDocTemplate) -> None:
    """Canvas callback to draw headers and footers on pages after the cover page."""
    canvas.saveState()
    # Bottom margin line
    canvas.setStrokeColor(colors.HexColor("#e2e8f0"))
    canvas.setLineWidth(0.75)
    canvas.line(54, 45, 558, 45)  # Margins are 54pt (0.75 in), width is 612pt

    # Running footer text
    canvas.setFont("Helvetica", 10)
    canvas.setFillColor(colors.HexColor("#64748b"))
    username_str = getattr(doc, "username", "Guest")
    if username_str and username_str.lower() != "guest":
        footer_text = f"{username_str} Board Game Collection"
    else:
        footer_text = "Board Game Collection"
    canvas.drawString(54, 30, footer_text)
    canvas.drawRightString(558, 30, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def draw_cover_page_decorations(
    canvas: Canvas, doc: SimpleDocTemplate
) -> None:
    """Canvas callback to draw first page background decoration or footer logo."""
    canvas.saveState()
    logo_path = Path("assets/powered-by-bgg-rgb.png")
    if logo_path.exists() and logo_path.is_file():
        # Draw logo image at bottom right
        # width = 120 pt, height = 26.75 pt (aspect ratio 498:111)
        # X = 558 - 120 = 438
        # Y = 45
        canvas.drawImage(
            str(logo_path),
            438,
            45,
            width=120,
            height=26.75,
            mask="auto",
        )
    canvas.restoreState()


def generate_catalog_pdf(
    session: Session,
    game_ids: list[bytes],
    output_stream: io.BytesIO,
    username: str = "Guest",
) -> None:
    """Generate a highly stylized, single-page-budget catalog PDF from the active game list.

    :param session: Active SQLModel database session.
    :param game_ids: List of binary Game IDs to include.
    :param output_stream: File-like bytes stream to write the PDF data to.
    :param username: The username of the user who owns the collection.
    """
    log.info(
        f"generate_catalog_pdf: Starting PDF generation for user '{username}' with {len(game_ids)} game IDs."
    )
    if not game_ids:
        # Generate an empty catalog document
        doc = SimpleDocTemplate(
            output_stream,
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54,
        )
        doc.username = username  # type: ignore[attr-defined] # ty:ignore[unresolved-attribute]
        styles = getSampleStyleSheet()
        style_empty = ParagraphStyle(
            "EmptyStyle", parent=styles["Heading2"], alignment=1
        )
        story: list[Flowable] = [
            Spacer(1, 100),
            Paragraph("No board games selected for export.", style_empty),
        ]
        doc.build(story)
        return

    # Load all games and their relationships
    games = session.exec(select(Game).where(Game.id.in_(game_ids))).all()  # type: ignore[attr-defined] # ty:ignore[unresolved-attribute]
    log.info(
        f"generate_catalog_pdf: Loaded {len(games)} game records from database."
    )
    export_game_ids = {g.id for g in games}
    id_to_game = {g.id: g for g in games}

    # Query all RelatedGame relationships (of any type) where both games are in the export list
    links = session.exec(
        select(RelatedGame)
        .where(RelatedGame.source_game_id.in_(list(export_game_ids)))  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
        .where(RelatedGame.target_game_id.in_(list(export_game_ids)))  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]
        .options(selectinload(cast("Any", RelatedGame.relationship_type)))
    ).all()

    # Build expansion_to_base mapping using ONLY "boardgameexpansion" relationships
    expansion_to_base = {}
    for link in links:
        if link.relationship_type.type == "boardgameexpansion":
            game_src = id_to_game[link.source_game_id]
            game_tgt = id_to_game[link.target_game_id]

            # Determine which is the base and which is the expansion.
            # Generally, the base game has a smaller BGG ID than the expansion.
            if game_src.bgg_id < game_tgt.bgg_id:
                base_id = game_src.id
                exp_id = game_tgt.id
            elif game_src.bgg_id > game_tgt.bgg_id:
                base_id = game_tgt.id
                exp_id = game_src.id
            else:
                # Fallback for identical bgg_id (e.g. mock games in unit tests)
                if len(game_src.name) < len(game_tgt.name):
                    base_id = game_src.id
                    exp_id = game_tgt.id
                elif len(game_src.name) > len(game_tgt.name):
                    base_id = game_tgt.id
                    exp_id = game_src.id
                else:
                    if game_src.id < game_tgt.id:
                        base_id = game_src.id
                        exp_id = game_tgt.id
                    else:
                        base_id = game_tgt.id
                        exp_id = game_src.id

            expansion_to_base[exp_id] = base_id

    # Build undirected adjacency list for connected components algorithm
    from collections import defaultdict

    adj = defaultdict(set)

    # 1. Add edges for all database relationship links (expansion, reimplementation, etc.)
    for link in links:
        adj[link.source_game_id].add(link.target_game_id)
        adj[link.target_game_id].add(link.source_game_id)

    # 2. Add edges for shared series/franchise family names
    family_to_games = defaultdict(list)
    for g in games:
        for fam in g.families:
            if fam.name.startswith("Game:") or fam.name.startswith("Series:"):
                family_to_games[fam.name].append(g.id)

    for g_ids in family_to_games.values():
        if len(g_ids) > 1:
            first_id = g_ids[0]
            for other_id in g_ids[1:]:
                adj[first_id].add(other_id)
                adj[other_id].add(first_id)

    # Find connected components using BFS
    visited = set()
    components = []
    for g_id in export_game_ids:
        if g_id not in visited:
            component = []
            queue = [g_id]
            visited.add(g_id)
            while queue:
                curr = queue.pop(0)
                component.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited and neighbor in export_game_ids:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(component)

    log.info(
        f"generate_catalog_pdf: Grouped {len(games)} games into {len(components)} connected components."
    )

    # Order each component and sort the components
    ordered_components = []
    for comp_ids in components:
        comp_games = [id_to_game[g_id] for g_id in comp_ids]

        # Separate base games vs expansions within this component
        comp_base_games = []
        comp_expansions = []
        for g in comp_games:
            parent_id = expansion_to_base.get(g.id)
            if parent_id and parent_id in export_game_ids:
                comp_expansions.append(g)
            else:
                comp_base_games.append(g)

        # Sort base games chronologically
        comp_base_games.sort(
            key=lambda g: (g.release_year or 0, g.name.lower())
        )

        # Map each base game in the component to its sorted list of expansions
        base_to_exps = defaultdict(list)
        for exp in comp_expansions:
            p_id = expansion_to_base[exp.id]
            base_to_exps[p_id].append(exp)

        for b_id in base_to_exps:
            base_to_exps[b_id].sort(key=lambda g: g.name.lower())

        # Build final ordered list for this component
        comp_ordered = []
        for bg in comp_base_games:
            comp_ordered.append(bg)
            if bg.id in base_to_exps:
                comp_ordered.extend(base_to_exps[bg.id])

        # Append any orphaned expansions just in case (their base game is not in the export list)
        orphan_exps = [
            exp
            for exp in comp_expansions
            if expansion_to_base[exp.id] not in export_game_ids
        ]
        orphan_exps.sort(key=lambda g: g.name.lower())
        comp_ordered.extend(orphan_exps)

        # Determine sort key for this component
        prim_fam = None
        for g in comp_games:
            fam_game = next(
                (f.name for f in g.families if f.name.startswith("Game:")),
                None,
            )
            fam_series = next(
                (f.name for f in g.families if f.name.startswith("Series:")),
                None,
            )
            prim_fam = fam_game or fam_series
            if prim_fam:
                break

        if prim_fam:
            if prim_fam.startswith("Game:"):
                sort_key = prim_fam[len("Game:") :].strip().lower()
            else:
                sort_key = prim_fam[len("Series:") :].strip().lower()
        else:
            # Fallback to the first base game name or first game name
            sort_key = (
                comp_base_games[0].name.lower()
                if comp_base_games
                else comp_games[0].name.lower()
            )

        ordered_components.append((sort_key, comp_ordered))

    # Sort components alphabetically by their sorting key
    ordered_components.sort(key=lambda x: x[0])

    # Concatenate all ordered games and track the "main" base game of each component
    main_game_ids = set()
    ordered_games = []
    for _, comp_ordered in ordered_components:
        # Find the first base game in this component
        first_base = next(
            (
                g
                for g in comp_ordered
                if not (
                    expansion_to_base.get(g.id)
                    and expansion_to_base.get(g.id) in export_game_ids
                )
            ),
            None,
        )
        if first_base:
            main_game_ids.add(first_base.id)
        ordered_games.extend(comp_ordered)

    # Cover Page Images Selection (up to 6 covers)
    cover_images = []
    for g in ordered_games:
        if g.image_path:
            img_path = IMAGE_DIR / g.image_path
            if img_path.exists() and img_path.is_file():
                cover_images.append(img_path)
                if len(cover_images) == 6:
                    break

    # Initialize Document
    doc = SimpleDocTemplate(
        output_stream,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    doc.username = username  # type: ignore[attr-defined] # ty:ignore[unresolved-attribute]

    # Custom Paragraph Styles
    style_cover_title = ParagraphStyle(
        "CoverTitle",
        fontName="Helvetica-Bold",
        fontSize=34,
        leading=40,
        alignment=1,  # Center
        textColor=colors.HexColor("#0f172a"),
    )

    # style_cover_subtitle = ParagraphStyle(
    #     "CoverSubtitle",
    #     fontName="Helvetica-Bold",
    #     fontSize=15,
    #     leading=18,
    #     alignment=1,  # Center
    #     textColor=colors.HexColor("#d97706"),  # Gold
    # )

    style_cover_meta = ParagraphStyle(
        "CoverMeta",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        alignment=1,  # Center
        textColor=colors.HexColor("#64748b"),
    )

    style_index_header = ParagraphStyle(
        "IndexHeader",
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
    )

    style_index_label = ParagraphStyle(
        "IndexLabel",
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1e293b"),
    )

    style_index_page = ParagraphStyle(
        "IndexPage",
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        alignment=2,  # Right
        textColor=colors.HexColor("#475569"),
    )

    style_game_title = ParagraphStyle(
        "GameTitle",
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#0f172a"),
    )

    style_game_subtitle = ParagraphStyle(
        "GameSubtitle",
        fontName="Helvetica-Oblique",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#475569"),
    )

    style_body = ParagraphStyle(
        "BodyStyle",
        fontName="Helvetica",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#334155"),
    )

    style_desc_header = ParagraphStyle(
        "DescHeader",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=17,
        textColor=colors.HexColor("#0f172a"),
    )

    story = []

    username_clean = safe_xml_text(username)
    if username_clean and username_clean.lower() != "guest":
        cover_title = f"{username_clean} Board Game Collection"
    else:
        cover_title = "Board Game Collection"

    # --- 1. COVER PAGE ---
    story.append(Spacer(1, 40))
    story.append(Paragraph(cover_title, style_cover_title))
    story.append(Spacer(1, 40))

    if cover_images:
        # Build Cover Grid Table (up to 3x2, max 6 images)
        grid_data = []
        num_rows = math.ceil(len(cover_images) / 3)
        for r in range(num_rows):
            row: list[RLImage | Table | str] = []
            for c in range(3):
                idx = r * 3 + c
                if idx < len(cover_images):
                    rl_img: RLImage | Table | None = get_scaled_image(
                        cover_images[idx], 90, 90
                    )
                    if not rl_img:
                        rl_img = get_image_fallback(90, 90)
                    row.append(rl_img)
                else:
                    row.append("")
            grid_data.append(row)

        grid_table = Table(
            grid_data, colWidths=[110, 110, 110], rowHeights=[110] * num_rows
        )
        grid_table.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ])
        )
        story.append(grid_table)
        story.append(Spacer(1, 40))
    else:
        # Elegant geometric spacer fallback
        decor_table = Table([[""]], colWidths=[330], rowHeights=[150])
        decor_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ])
        )
        story.append(decor_table)
        story.append(Spacer(1, 80))

    current_date = datetime.now().strftime("%B %d, %Y")
    story.append(
        Paragraph(
            f"Curated Library Compendium<br/>A collection of {len(ordered_games)} titles",
            style_cover_meta,
        )
    )
    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            f"Generated on {current_date} via Spielpendium", style_cover_meta
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "<a href='https://spielpendium.com'><font color='#3b82f6'>spielpendium.com</font></a>",
            style_cover_meta,
        )
    )
    story.append(Spacer(1, 15))

    # Generate QR Code for spielpendium.com
    qr_code = QrCodeWidget("https://spielpendium.com")
    qr_code.barWidth = 150
    qr_code.barHeight = 150
    qr_draw = Drawing(150, 150)
    qr_draw.add(qr_code)
    qr_draw.hAlign = "CENTER"
    story.append(qr_draw)

    story.append(PageBreak())

    # --- 2. INDEX / TABLE OF CONTENTS ---
    items_per_page = 30
    num_index_pages = (
        math.ceil(len(ordered_games) / items_per_page) if ordered_games else 1
    )

    log.info(
        f"generate_catalog_pdf: Generating cover page with {len(cover_images)} covers. "
        f"TOC will contain {len(ordered_games)} entries across {num_index_pages} index pages."
    )

    base_game_counter = 0
    index_entries = []
    for idx, game in enumerate(ordered_games):
        page_num = 2 + num_index_pages + idx
        parent_id = expansion_to_base.get(game.id)
        is_exp = parent_id is not None and parent_id in export_game_ids
        game_anchor = f"game_{game.id.hex()}"

        if not is_exp:
            # Only number the primary "main" base game of the component
            if game.id in main_game_ids:
                base_game_counter += 1
                label = f"<a href='#{game_anchor}'><b>{base_game_counter}. {safe_xml_text(game.name)}</b></a>"
            else:
                label = f"<a href='#{game_anchor}'><b>&nbsp;&nbsp;&nbsp;&nbsp;• {safe_xml_text(game.name)}</b></a>"
            page_str = f"<a href='#{game_anchor}'><b>Page {page_num}</b></a>"
        else:
            label = f"<a href='#{game_anchor}'><font color='#475569'>&nbsp;&nbsp;&nbsp;&nbsp;• {safe_xml_text(game.name)}</font></a>"
            page_str = f"<a href='#{game_anchor}'><font color='#475569'>Page {page_num}</font></a>"

        index_entries.append((label, page_str))

    # Output index chunks
    for i in range(0, len(index_entries), items_per_page):
        chunk = index_entries[i : i + items_per_page]

        story.append(Paragraph("Table of Contents", style_index_header))
        story.append(Spacer(1, 12))

        table_data = []
        for label, page_str in chunk:
            table_data.append([
                Paragraph(label, style_index_label),
                Paragraph(page_str, style_index_page),
            ])

        t = Table(table_data, colWidths=[400, 104])
        t.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ])
        )
        story.append(t)
        story.append(PageBreak())

    # --- 3. CATALOG PAGES (Exactly 1 page per game) ---
    for idx, game in enumerate(ordered_games, 1):
        log.debug(
            f"generate_catalog_pdf: Rendering page for game {idx}/{len(ordered_games)}: '{game.name}'"
        )
        # Title section with anchor for Table of Contents link
        anchor = f"<a name='game_{game.id.hex()}'/>"
        story.append(
            Paragraph(anchor + safe_xml_text(game.name), style_game_title)
        )
        if game.sub_name:
            sub_name_raw = game.sub_name.strip()

            def is_compatible(text: str) -> bool:
                try:
                    normalize_special_chars(text).encode("latin-1")
                    return True
                except UnicodeEncodeError:
                    return False

            if "," in sub_name_raw:
                sub_names_raw_list = [
                    n.strip() for n in sub_name_raw.split(",") if n.strip()
                ]
            else:
                sub_names_raw_list = [sub_name_raw] if sub_name_raw else []

            sub_names_list = [
                normalize_special_chars(name)
                for name in sub_names_raw_list
                if is_compatible(name)
            ]

            if sub_names_list:
                if len(sub_names_list) > 3:
                    sub_name_display = (
                        ", ".join(sub_names_list[:3])
                        + f" (+{len(sub_names_list) - 3} more)"
                    )
                else:
                    sub_name_display = ", ".join(sub_names_list)

                # Enforce hard length limit to prevent line overflow
                if len(sub_name_display) > 120:
                    sub_name_display = sub_name_display[:120] + "..."

                story.append(
                    Paragraph(
                        safe_xml_text(sub_name_display), style_game_subtitle
                    )
                )
        story.append(Spacer(1, 15))

        # Top section: image on left, metadata key-value table on right
        game_img: RLImage | Table | None = None
        if game.image_path:
            img_path = IMAGE_DIR / game.image_path
            game_img = get_scaled_image(img_path, 160, 160)

        if not game_img:
            game_img = get_image_fallback(160, 160)

        meta_table = make_metadata_table(game, style_body)

        top_table_data = [[game_img, meta_table]]
        top_table = Table(top_table_data, colWidths=[170, 334])
        top_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ])
        )
        story.append(top_table)
        story.append(Spacer(1, 20))

        # Divider line
        divider = Table([[""]], colWidths=[504], rowHeights=[1])
        divider.setStyle(
            TableStyle([
                ("LINEABOVE", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ])
        )
        story.append(divider)
        story.append(Spacer(1, 15))

        # Bottom section: Game Description
        story.append(Paragraph("Game Description:", style_desc_header))
        story.append(Spacer(1, 8))

        # Safe Description with Truncation (Page Budget Protection: limit chars and lines)
        desc_raw = game.description or "No description available."

        # Collapse consecutive empty lines and limit total line count
        raw_lines = desc_raw.splitlines()
        cleaned_lines = []
        consecutive_empty = 0
        for line in raw_lines:
            line_str = line.strip()
            if not line_str:
                consecutive_empty += 1
                if consecutive_empty <= 1:
                    cleaned_lines.append("")
            else:
                consecutive_empty = 0
                cleaned_lines.append(line)

        max_lines = 20
        if len(cleaned_lines) > max_lines:
            desc_text = "\n".join(cleaned_lines[: max_lines - 1]) + "\n..."
        else:
            desc_text = "\n".join(cleaned_lines)

        max_desc_len = 1200
        if len(desc_text) > max_desc_len:
            desc_text = desc_text[:max_desc_len] + "..."

        story.append(Paragraph(safe_xml_text(desc_text), style_body))
        story.append(PageBreak())

    # Build the document, passing the canvas footer callback for page numbers and margins
    log.info("generate_catalog_pdf: Building PDF document (doc.build)...")
    doc.build(
        story,
        onFirstPage=draw_cover_page_decorations,
        onLaterPages=draw_later_page_footer,
    )
    log.info("generate_catalog_pdf: PDF catalog successfully compiled.")
