# Board Game Collection Web App - Task List

This document outlines the tasks required to build the web application for browsing a board game collection, displaying detailed game information, and navigating associated games.

**Ultimate Goal:** Create a web app with a card-based UI for each game in the collection. Clicking a card should load a separate page or modal popup with detailed game information (description, player info, complexity, associated games). Associated games should be clickable and indicate if they are in the user's collection.

---

## Phase 1: Database & Data Ingestion Refinement
*(Goal: Ensure the SQLModel schema can store all necessary BGG data and the API client can populate it.)*

*   **Task 1.1: Update `Game` Model for `bgg_id`**
    *   **Status:** **COMPLETED** (Added `bgg_id: int = Field(unique=True, index=True, nullable=False)` to `Game` model in `util/database/models.py`).
    *   **Description:** The `Game` model now has a separate `bgg_id` field for the integer ID from BoardGameGeek, distinct from the internal binary UUID `id`.
    *   **Next Action:** Ensure `api/bgg_api_interface.py` correctly uses `bgg_id` when fetching/saving games.

*   **Task 1.2: Enhance `save_collection_data_to_db` for Full Game Data**
    *   **Description:** Currently, when a new `Game` is encountered via `get_user_game_collection`, only minimal placeholder data is saved. This needs to be updated to use the new `bgg_id` and fetch full game details.
    *   **Action:** Modify `api/bgg_api_interface.py::save_collection_data_to_db` to:
        *   Use `item_data.get('@objectid')` for the `bgg_id` when checking for existing games or creating new ones.
        *   For any *new* game, call `get_game_info` to fetch its full details using the `bgg_id`.
        *   Then, populate *all* relevant fields in the `Game` model (description, min/max players, complexity, release year, image, etc.) based on the `get_game_info` response.
    *   **Dependencies:** `get_game_info`'s output structure and all fields in the `Game` model.
    *   **Note:** This might involve an asynchronous task or a batch process if fetching details for many new games at once is slow.

*   **Task 1.3: Implement `save_game_details_to_db`**
    *   **Description:** Create a dedicated function to process the detailed `dict` output from `get_game_info` (the BGG `/thing` endpoint) and update/create a `Game` model instance. This will be used by Task 1.2 and when loading individual game pages.
    *   **Action:** In `api/bgg_api_interface.py`, create `save_game_details_to_db(bgg_id: int, game_detail_data: dict[str, Any])`. This function should:
        *   Take the BGG game ID (integer) and the parsed API response.
        *   Find the `Game` in the DB by `bgg_id` or create it (assigning a new internal `id` UUID if created).
        *   Extract all relevant fields (name, description, players, complexity, publishers, categories, authors, artists, related games, etc.) from `game_detail_data` and update the `Game` model and its associated link tables (`PublisherGameLink`, `GameCategoryLink`, `PersonGameLink`, `RelatedGame`).
    *   **Dependencies:** Understanding BGG `/thing` XML structure and mapping to SQLModel fields.

*   **Task 1.4: Populate `RelatedGame` and Check Collection Status**
    *   **Description:** When `get_game_info` provides "related games" (expansions, reimplementations), these need to be stored in the `RelatedGame` table using *their* `bgg_id`s and linked to the `source_game_id` (the `id` of the current game).
    *   **Action:** Extend `save_game_details_to_db` to parse the associated game information from the API response and create/update entries in the `RelatedGame` table. When displaying in the UI, we'll need to query `CollectionItem` to see if the associated game is in the current user's collection.

---

## Phase 2: Core Dash Application Setup
*(Goal: Get a basic Dash application running with Mantine components.)*

*   **Task 2.1: Initialize Dash Application**
    *   **Description:** Set up the basic Dash application structure.
    *   **Action:** Create `app.py` (or your main Dash file) with `Dash(__name__, use_pages=True)` and a basic layout. Integrate `dash-mantine-components`.

*   **Task 2.2: Define App Layout and Navigation**
    *   **Description:** Create the main layout that will contain your collection view and potentially a header/footer.
    *   **Action:** Implement a `dmc.AppShell` or similar main layout. Use `dcc.Location` if you plan to have separate pages for game details, or stick with modals if it's all within one page.

---

## Phase 3: Collection View UI & Data Display
*(Goal: Display the user's game collection as interactive cards.)*

*   **Task 3.1: Fetch Collection Data for UI**
    *   **Description:** In your Dash app, fetch the user's collection from the database using your `get_user_game_collection` function.
    *   **Action:** Implement a Dash callback that triggers on app load (or user login) to call `get_user_game_collection` and store the `Collection` object (or its serialized form) in a `dcc.Store` component.

*   **Task 3.2: Create Game Card Component**
    *   **Description:** Design a reusable UI component for a single game in the collection.
    *   **Action:** Create a Python function that returns a `dmc.Card` (or similar) for a `Game` object, displaying its name, image, and maybe a few key stats (e.g., min players, complexity). Each card should have a unique ID that uses the `Game.bgg_id` to identify which game was clicked.

*   **Task 3.3: Render Dynamic Collection Grid**
    *   **Description:** Display all games from the fetched collection in a grid or flex layout.
    *   **Action:** Implement a Dash callback that takes the data from the `dcc.Store` (from Task 3.1) and generates a layout of `dmc.Grid` containing multiple Game Card components (from Task 3.2).

---

## Phase 4: Game Detail Popup/Page
*(Goal: Show comprehensive information for a selected game.)*

*   **Task 4.1: Implement Click Callback for Game Cards**
    *   **Description:** When a user clicks on a game card, trigger an action to show its details.
    *   **Action:** Create a Dash callback with `Input` on the game cards (using `ctx.triggered_id` or similar for dynamic IDs based on `Game.bgg_id`) that will open a `dmc.Modal` or navigate to a new page (e.g., `/game/<bgg_id>`).

*   **Task 4.2: Fetch and Display Detailed Game Information**
    *   **Description:** Retrieve the full game details from the database (or API if not fully saved yet) and display them in the popup/page.
    *   **Action:** In the card click callback (Task 4.1), use `get_game_info` (which should leverage `save_game_details_to_db` or query the DB directly) to get the `Game` object for the clicked `bgg_id`. Populate the modal/page with description, player info, complexity, etc.

*   **Task 4.3: Display Associated Games with Collection Status**
    *   **Description:** Within the detail view, list related games and indicate if the user owns them.
    *   **Action:** Extend the detail view component to:
        *   Query the `RelatedGame` table for games associated with the current game.
        *   For each associated game, query `CollectionItem` to check if `current_user_collection_id` and `associated_game_id` exists.
        *   Display the associated game names, perhaps with a small icon or text indicating "In Collection."

---

## Phase 5: Navigation for Associated Games
*(Goal: Allow seamless navigation between related game detail views.)*

*   **Task 5.1: Implement Click Callback for Associated Games**
    *   **Description:** Make the associated game names clickable within the detail view.
    *   **Action:** For each associated game displayed in the detail view, wrap its display in a `dmc.Anchor` or `html.Button` with an ID that allows it to be clicked. Implement a callback that captures these clicks, using the `bgg_id` of the associated game.

*   **Task 5.2: Update Detail View for Associated Games**
    *   **Description:** When an associated game is clicked, the detail view should update to show that game's information.
    *   **Action:** The callback from Task 5.1 should update the state of the detail view (e.g., update the URL, or update a `dcc.Store` containing the current detailed game `bgg_id`) to re-render the modal/page with the new game's information.

---

**Cross-Cutting Concerns:**

*   **Error Handling and Loading States**: Throughout the UI, implement `dmc.LoadingOverlay` or other indicators for API calls and database fetches. Add robust `try-except` blocks for all data operations.
*   **Logging**: Ensure consistent logging throughout `api/bgg_api_interface.py` and your Dash callbacks for easier debugging.
*   **`config.py`**: Make sure `config.py` is properly set up with `BGG_API_URL`, `BGG_API_TOKEN`, `DB_FILE`, and `DEBUG` for all environments.
*   **Styling**: Apply consistent styling using `dash-mantine-components` themeing.
