# Board Game Collection Web App - Task List

This document outlines the tasks required to build the web application for
browsing a board game collection, displaying detailed game information, and
navigating associated games.

**Ultimate Goal:** Create a web app with a card-based UI for each game in the
collection. Clicking a card should load a separate page or modal popup with
detailed game information (description, player info, complexity, associated
games). Associated games should be clickable and indicate if they are in the
user's collection.

---

## Phase 1: Database & Data Ingestion Refinement

*(Goal: Ensure the SQLModel schema can store all necessary BGG data and the API
client can populate it.)*

* **Task 1.1: Update `Game` Model for `bgg_id`**
    * **Status:** **COMPLETED**
    * **Description:** Added `bgg_id` and standardized UUID binary storage.
* **Task 1.2: Enhance `save_collection_data_to_db` for Full Game Data**
    * **Status:** **COMPLETED**
    * **Description:** Implemented batch fetching (20 games/request) and
      integrated with `_process_and_save_game_details`.
* **Task 1.3: Implement `save_game_details_to_db`**
    * **Status:** **COMPLETED**
    * **Description:** Created `_process_and_save_game_details` which parses
      nested BGG XML into a normalized relational schema.
* **Task 1.4: Populate `RelatedGame` and Check Collection Status**
    * **Status:** **COMPLETED**
    * **Description:** Successfully parsing expansions, accessories, and
      reimplementations into the `RelatedGame` link table.

---

## Phase 2: Core Dash Application Setup

*(Goal: Get a basic Dash application running with Mantine components.)*

* **Task 2.1: Initialize Dash Application**
    * **Status:** **COMPLETED**
    * **Description:** Set up the basic Dash application structure with Mantine
      components and layout.
* **Task 2.2: Define App Layout and Navigation**
    * **Status:** **COMPLETED**
    * **Description:** Created `app.py` with `dmc.AppShell`, sidebar, and
      `dash.register_page` routing.

---

## Phase 3: Collection View UI & Data Display

*(Goal: Display the user's game collection as interactive cards.)*

* **Task 3.1: Fetch Collection Data for UI**
    * **Status:** **COMPLETED**
    * **Description:** Implemented `get_user_game_collection` and basic loading
      logic in `pages/collection.py`.
* **Task 3.2: Create Game Card Component**
    * **Status:** **COMPLETED**
    * **Description:** Designed `create_game_card` using `dmc.Card` with binary
      thumbnail rendering.
* **Task 3.3: Render Dynamic Collection Grid**
    * **Status:** **COMPLETED**
    * **Description:** Implemented `update_grid` callback with `dmc.SimpleGrid`
      and loading overlays.

---

## Phase 4: Game Detail Popup/Page

*(Goal: Show comprehensive information for a selected game.)*

* **Task 4.1: Implement Click Callback for Game Cards**
    * **Status:** **COMPLETED**
    * **Description:** Implemented `open_modal` callback triggered by
      `game-card` indices.
* **Task 4.2: Fetch and Display Detailed Game Information**
    * **Status:** **COMPLETED**
    * **Description:** Modal renders full high-res image, description, stats,
      designers, and publishers.
* **Task 4.3: Display Associated Games with Collection Status**
    * **Status:** **COMPLETED**
    * **Description:** Within the detail view, list related games and indicate
      if the user owns them.

---

## Phase 5: Navigation for Associated Games

*(Goal: Allow seamless navigation between related game detail views.)*

* **Task 5.1: Implement Click Callback for Associated Games**
    * **Description:** Make the associated game names clickable within the
      detail view.
    * **Action:** For each associated game displayed in the detail view, wrap
      its display in a `dmc.Anchor` or `html.Button` with an ID that allows it
      to be clicked. Implement a callback that captures these clicks, using the
      `bgg_id` of the associated game.

* **Task 5.2: Update Detail View for Associated Games**
    * **Description:** When an associated game is clicked, the detail view
      should update to show that game's information.
    * **Action:** The callback from Task 5.1 should update the state of the
      detail view (e.g., update the URL, or update a `dcc.Store` containing the
      current detailed game `bgg_id`) to re-render the modal/page with the new
      game's information.

---

**Cross-Cutting Concerns:**

* **Testing & Quality Assurance**:
    * **Status:** **IN PROGRESS**
    * **Action:** Implemented `pytest` suite for BGG ingestion, binary image
      handling, and collection synchronization.
* **Error Handling and Loading States**: Throughout the UI, implement
  `dmc.LoadingOverlay` or other indicators for API calls and database fetches.
  Add robust `try-except` blocks for all data operations.
* **Logging**: Ensure consistent logging throughout `api/bgg_api_interface.py`
  and your Dash callbacks for easier debugging.
* **`config.py`**: Make sure `config.py` is properly set up with `BGG_API_URL`,
  `BGG_API_TOKEN`, `DB_FILE`, and `DEBUG` for all environments.
* **Styling**: Apply consistent styling using `dash-mantine-components`
  themeing.
