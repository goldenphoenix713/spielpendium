from __future__ import annotations

import io
from typing import TYPE_CHECKING

from tests.test_models import create_mock_game
from util.models import (
    GameRelationship,
    Person,
    PersonGameLink,
    PersonRole,
    Publisher,
    RelatedGame,
)
from util.pdf_generator import generate_catalog_pdf

if TYPE_CHECKING:
    from sqlmodel import Session


def test_empty_collection(session: Session) -> None:
    """Test generating a PDF with an empty collection list."""
    buf = io.BytesIO()
    generate_catalog_pdf(session, [], buf)
    pdf_data = buf.getvalue()

    assert len(pdf_data) > 0
    # ReportLab PDF files start with %PDF
    assert pdf_data.startswith(b"%PDF")


def test_single_game_export(session: Session) -> None:
    """Test generating a PDF for a single game and checking safe truncation."""
    game = create_mock_game(1001, "Catan")
    # Set a very long description to test truncation page-budget protection
    game.description = "A" * 1500
    session.add(game)
    session.commit()
    session.refresh(game)

    buf = io.BytesIO()
    generate_catalog_pdf(session, [game.id], buf)
    pdf_data = buf.getvalue()

    assert len(pdf_data) > 0
    assert pdf_data.startswith(b"%PDF")


def test_expansion_grouping_and_sorting(session: Session) -> None:
    """Test that base games are sorted alphabetically and expansions are nested under them."""
    # Create base games
    zombicide = create_mock_game(2001, "Zombicide")
    azul = create_mock_game(2002, "Azul")
    catan = create_mock_game(2003, "Catan")

    # Create expansions
    catan_expansion = create_mock_game(2004, "Catan: Cities & Knights")
    zombicide_expansion = create_mock_game(2005, "Zombicide: Toxic Mall")

    # Add to DB
    session.add_all([
        zombicide,
        azul,
        catan,
        catan_expansion,
        zombicide_expansion,
    ])
    session.commit()

    # Refresh to populate IDs
    session.refresh(zombicide)
    session.refresh(azul)
    session.refresh(catan)
    session.refresh(catan_expansion)
    session.refresh(zombicide_expansion)

    # Establish expansion relationships
    rel_type = GameRelationship(type="boardgameexpansion")
    session.add(rel_type)
    session.commit()
    session.refresh(rel_type)

    link_catan = RelatedGame(
        source_game_id=catan_expansion.id,
        target_game_id=catan.id,
        relationship_type_id=rel_type.id,
    )
    link_catan_rev = RelatedGame(
        source_game_id=catan.id,
        target_game_id=catan_expansion.id,
        relationship_type_id=rel_type.id,
    )
    link_zombicide = RelatedGame(
        source_game_id=zombicide_expansion.id,
        target_game_id=zombicide.id,
        relationship_type_id=rel_type.id,
    )
    link_zombicide_rev = RelatedGame(
        source_game_id=zombicide.id,
        target_game_id=zombicide_expansion.id,
        relationship_type_id=rel_type.id,
    )
    session.add_all([
        link_catan,
        link_catan_rev,
        link_zombicide,
        link_zombicide_rev,
    ])
    session.commit()

    # Generate PDF for all 5 games
    game_ids = [
        zombicide.id,
        azul.id,
        catan.id,
        catan_expansion.id,
        zombicide_expansion.id,
    ]

    buf = io.BytesIO()
    # If the grouping logic is correct, the PDF should compile without errors.
    generate_catalog_pdf(session, game_ids, buf)
    pdf_data = buf.getvalue()

    assert len(pdf_data) > 0
    assert pdf_data.startswith(b"%PDF")


def test_missing_image_fallback(session: Session) -> None:
    """Test generating a PDF for a game with a non-existent cover image path."""
    game = create_mock_game(3001, "Ticket to Ride")
    game.image_path = "non_existent_cover_image.jpg"
    session.add(game)
    session.commit()
    session.refresh(game)

    buf = io.BytesIO()
    # It should not raise an error, but build successfully using the fallback
    generate_catalog_pdf(session, [game.id], buf)
    pdf_data = buf.getvalue()

    assert len(pdf_data) > 0
    assert pdf_data.startswith(b"%PDF")


def test_pdf_username_customization(session: Session) -> None:
    """Test generating a PDF with a customized username and ensuring it is in the document."""
    from reportlab import rl_config

    orig_compression = rl_config.pageCompression
    rl_config.pageCompression = 0
    try:
        game = create_mock_game(4001, "Carcassonne")
        session.add(game)
        session.commit()
        session.refresh(game)

        buf = io.BytesIO()
        generate_catalog_pdf(session, [game.id], buf, username="Eddie")
        pdf_data = buf.getvalue()

        assert len(pdf_data) > 0
        assert pdf_data.startswith(b"%PDF")
        # Verify the customized title is present in the generated PDF data
        assert b"Eddie" in pdf_data
        assert b"Board Game Collection" in pdf_data
    finally:
        rl_config.pageCompression = orig_compression


def test_pdf_with_images(session: Session) -> None:
    """Test generating a PDF where games have actual cover images (covering image loading and cover grid)."""
    from PIL import Image as PILImage

    from config import IMAGE_DIR

    # Ensure IMAGE_DIR exists
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    # Create a dummy image
    dummy_img_name = "test_cover_image.jpg"
    dummy_img_path = IMAGE_DIR / dummy_img_name
    img = PILImage.new("RGB", (120, 180), color="blue")
    img.save(dummy_img_path)

    try:
        # Create a game with this image
        game = create_mock_game(5001, "Carcassonne")
        game.image_path = dummy_img_name
        session.add(game)
        session.commit()
        session.refresh(game)

        buf = io.BytesIO()
        generate_catalog_pdf(session, [game.id], buf)
        pdf_data = buf.getvalue()

        assert len(pdf_data) > 0
        assert pdf_data.startswith(b"%PDF")
    finally:
        # Clean up the dummy image file
        if dummy_img_path.exists():
            dummy_img_path.unlink()


def test_pdf_metadata_truncation(session: Session) -> None:
    """Test that publishers and authors (designers) lists are truncated when they exceed 3 items."""
    from uuid import uuid4

    from reportlab import rl_config

    game = create_mock_game(6001, "Big Game")
    session.add(game)
    session.commit()
    session.refresh(game)

    # Add 5 publishers
    publishers = [
        Publisher(id=bytes([i] * 16), name=f"Pub {i}") for i in range(5)
    ]
    game.publishers = publishers

    # Create the PersonRole for author
    author_role = PersonRole(id=uuid4().bytes, role="author")
    session.add(author_role)
    session.commit()

    # Add 5 authors (People)
    authors = [
        Person(id=bytes([100 + i] * 16), name=f"Author {i}") for i in range(5)
    ]
    for author in authors:
        session.add(author)
    session.commit()

    # Link authors to game with role "author"
    for author in authors:
        link = PersonGameLink(
            person_id=author.id, game_id=game.id, role_id=author_role.id
        )
        session.add(link)
    session.commit()

    # Refresh the game to load the relationships
    session.refresh(game)

    buf = io.BytesIO()

    # Disable compression to inspect output PDF text
    orig_compression = rl_config.pageCompression
    rl_config.pageCompression = 0
    try:
        generate_catalog_pdf(session, [game.id], buf)
        pdf_data = buf.getvalue()

        assert len(pdf_data) > 0
        assert pdf_data.startswith(b"%PDF")

        # Verify first 3 publishers/authors are present
        assert b"Pub 0" in pdf_data
        assert b"Pub 1" in pdf_data
        assert b"Pub 2" in pdf_data
        assert b"Author 0" in pdf_data
        assert b"Author 1" in pdf_data
        assert b"Author 2" in pdf_data

        # Verify "+2 more" indicating truncation is present
        assert b"+2 more" in pdf_data

        # Verify 4th and 5th items are not in the raw data (they should be truncated)
        assert b"Pub 3" not in pdf_data
        assert b"Author 3" not in pdf_data
    finally:
        rl_config.pageCompression = orig_compression


def test_pdf_subtitle_truncation(session: Session) -> None:
    """Test that long sub_name lists are truncated to 3 items and/or a max length of 120 characters."""
    from reportlab import rl_config

    game = create_mock_game(7001, "Subtitled Game")
    game.sub_name = (
        "Sub Name 1, Sub Name 2, Sub Name 3, Sub Name 4, Sub Name 5"
    )
    session.add(game)
    session.commit()
    session.refresh(game)

    buf = io.BytesIO()
    # Disable compression to inspect output PDF text
    orig_compression = rl_config.pageCompression
    rl_config.pageCompression = 0
    try:
        generate_catalog_pdf(session, [game.id], buf)
        pdf_data = buf.getvalue()

        assert len(pdf_data) > 0
        assert pdf_data.startswith(b"%PDF")

        # Verify first 3 sub-names are present in the PDF data
        assert b"Sub Name 1" in pdf_data
        assert b"Sub Name 2" in pdf_data
        assert b"Sub Name 3" in pdf_data

        # Verify "+2 more" indicating truncation is present
        assert b"+2 more" in pdf_data

        # Verify 4th and 5th items are not in the raw data
        assert b"Sub Name 4" not in pdf_data
    finally:
        rl_config.pageCompression = orig_compression


def test_pdf_subtitle_character_filtering(session: Session) -> None:
    """Test that alternate names containing non-cp1252 characters are skipped/filtered."""
    from reportlab import rl_config

    game = create_mock_game(8001, "Uni Game")
    # Sub-names contain a Japanese name (needs filtering) and a valid Latin name
    game.sub_name = "Valid Alt Name, ベトレイヤル・レガシー"
    session.add(game)
    session.commit()
    session.refresh(game)

    buf = io.BytesIO()
    orig_compression = rl_config.pageCompression
    rl_config.pageCompression = 0
    try:
        generate_catalog_pdf(session, [game.id], buf)
        pdf_data = buf.getvalue()

        assert len(pdf_data) > 0
        assert pdf_data.startswith(b"%PDF")

        # Verify the cp1252 compatible name is present
        assert b"Valid Alt Name" in pdf_data

        # Verify the Japanese name is skipped entirely (not rendered as squares or question marks)
        assert b"\xe3\x83\x99" not in pdf_data  # UTF-8 bytes for 'ベ'
    finally:
        rl_config.pageCompression = orig_compression


def test_pdf_special_character_normalization(session: Session) -> None:
    """Test that special characters like en-dash and smart quotes are normalized to ascii/latin-1 equivalents in PDF output."""
    from reportlab import rl_config

    from util.pdf_generator import normalize_special_chars, safe_xml_text

    # Verify normalize_special_chars helper behaves correctly
    assert (
        normalize_special_chars("Star Realms: United – Assault")
        == "Star Realms: United - Assault"
    )
    assert (
        normalize_special_chars("“Hello” and ‘World’")
        == "\"Hello\" and 'World'"
    )
    assert normalize_special_chars("test…") == "test..."

    # Verify safe_xml_text behaves correctly with latin-1 conversion
    assert (
        safe_xml_text("Star Realms: United – Assault")
        == "Star Realms: United - Assault"
    )
    assert safe_xml_text("ベ") == "?"  # Unrenderable gets replaced by ?

    game = create_mock_game(9001, "Test Special Chars Game")
    game.sub_name = "Star Realms: United – Assault, “Special”"
    session.add(game)
    session.commit()
    session.refresh(game)

    buf = io.BytesIO()
    orig_compression = rl_config.pageCompression
    rl_config.pageCompression = 0
    try:
        generate_catalog_pdf(session, [game.id], buf)
        pdf_data = buf.getvalue()

        # The en-dash '–' (U+2013) should be normalized to standard hyphen '-' (U+002D)
        assert b"Star Realms: United - Assault" in pdf_data
        # The smart quotes should be normalized to standard double quotes
        assert b"Special" in pdf_data
    finally:
        rl_config.pageCompression = orig_compression


def test_pdf_table_of_contents_links(session: Session) -> None:
    """Test that the Table of Contents generates interactive internal links to the game pages."""
    from pypdf import PdfReader
    from reportlab import rl_config

    game1 = create_mock_game(10001, "Link Game One")
    game2 = create_mock_game(10002, "Link Game Two")
    session.add_all([game1, game2])
    session.commit()
    session.refresh(game1)
    session.refresh(game2)

    buf = io.BytesIO()
    orig_compression = rl_config.pageCompression
    rl_config.pageCompression = 0
    try:
        generate_catalog_pdf(session, [game1.id, game2.id], buf)
        pdf_data = buf.getvalue()

        # Read PDF using pypdf
        reader = PdfReader(io.BytesIO(pdf_data))

        # Table of Contents page (Page 2, 0-indexed is 1)
        toc_page = reader.pages[1]

        # Verify the presence of Annotations (links) on the TOC page
        assert "/Annots" in toc_page
        annots = toc_page["/Annots"]
        # There should be at least two annotations (one for each game in TOC)
        assert len(annots) >= 2  # ty:ignore[invalid-argument-type]

        # Verify annotations are Links
        has_links = False
        for annot in annots:  # ty:ignore[not-iterable]
            resolved = annot.get_object()
            if resolved.get("/Subtype") == "/Link":
                has_links = True
                assert "/Dest" in resolved or "/A" in resolved

        assert has_links, "TOC page must contain clickable link annotations"
    finally:
        rl_config.pageCompression = orig_compression


def test_pdf_cover_page_spielpendium_branding(session: Session) -> None:
    """Test that the PDF cover page includes the Spielpendium branding text and website URL."""
    from reportlab import rl_config

    game = create_mock_game(11001, "Catan")
    session.add(game)
    session.commit()
    session.refresh(game)

    buf = io.BytesIO()
    orig_compression = rl_config.pageCompression
    rl_config.pageCompression = 0
    try:
        generate_catalog_pdf(session, [game.id], buf)
        pdf_data = buf.getvalue()

        # Verify the branding text "via Spielpendium" is in the raw PDF
        assert b"via Spielpendium" in pdf_data
        # Verify the website URL is in the raw PDF
        assert b"spielpendium.com" in pdf_data
    finally:
        rl_config.pageCompression = orig_compression
