from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

# Add project root to PYTHONPATH
sys.path.append(str(Path(__file__).parents[1]))

from sqlmodel import Session, select

from util.models import Game, engine
from util.pdf_generator import generate_catalog_pdf


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a board game catalog PDF from the spielpendium database."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="exports/board_game_catalog.pdf",
        help="Path where the output PDF should be saved (default: exports/board_game_catalog.pdf).",
    )
    parser.add_argument(
        "--username",
        "-u",
        type=str,
        default="Guest",
        help="The username to display on the cover page and footer (default: Guest).",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=None,
        help="Limit the number of games exported to the PDF (useful for testing).",
    )

    args = parser.parse_args()

    output_path = Path(args.output)
    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Connecting to database...")
    with Session(engine) as session:
        # Determine if we should query a specific user's collection or all games
        if args.username and args.username.lower() != "guest":
            from api import get_user_game_collection

            collection = get_user_game_collection(args.username)
            if not collection or not collection.items:
                print(
                    f"No collection found for user '{args.username}'. Exiting."
                )
                sys.exit(1)

            # Extract game IDs from collection items
            items = [item for item in collection.items if item.game]
            # Sort games alphabetically by name
            items.sort(key=lambda item: item.game.name.lower())
            game_ids = [item.game_id for item in items]
        else:
            # Fetch all game IDs ordered by name
            stmt = select(Game.id).order_by(Game.name)
            game_ids = list(session.exec(stmt).all())

        if args.limit is not None:
            game_ids = game_ids[: args.limit]

        if not game_ids:
            print("No games found in the database. Exiting.")
            sys.exit(1)

        print(f"Found {len(game_ids)} games to compile.")
        print(f"Compiling PDF for user '{args.username}'...")

        # We generate PDF to memory stream first
        buffer = io.BytesIO()
        generate_catalog_pdf(session, game_ids, buffer, username=args.username)

        # Write buffer to output file
        with open(output_path, "wb") as f:
            f.write(buffer.getvalue())

    print(
        f"Success! PDF catalog successfully generated and saved to: {output_path}"
    )


if __name__ == "__main__":
    main()
