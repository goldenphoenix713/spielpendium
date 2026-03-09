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
    * **Description:** Designed `create_game_card` using `dmc.Card` with local
      image caching rendering.
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
    * **Status:** **COMPLETED**
    * **Description:** Make the associated game names clickable within the
      detail view.
    * **Action:** For each associated game displayed in the detail view, wrap
      its display in a `dmc.Anchor` or `html.Button` with an ID that allows it
      to be clicked. Implement a callback that captures these clicks, using the
      `bgg_id` of the associated game.

* **Task 5.2: Update Detail View for Associated Games**
    * **Status:** **COMPLETED**
    * **Description:** When an associated game is clicked, the detail view
      should update to show that game's information.
    * **Action:** The callback from Task 5.1 should update the state of the
      detail view (e.g., update the URL, or update a `dcc.Store` containing the
      current detailed game `bgg_id`) to re-render the modal/page with the new
      game's information.

---

**Cross-Cutting Concerns:**

* **Testing & Quality Assurance**:
    * **Status:** **COMPLETED**
    * **Action:** Implemented comprehensive `pytest` suite covering BGG ingestion, local image caching, collection sync, and UI callbacks. Added full type annotations to all test modules.
* **Error Handling and Loading States**: Throughout the UI, implement
  `dmc.LoadingOverlay` or other indicators for API calls and database fetches.
  Add robust `try-except` blocks for all data operations.
* **Logging**: Ensure consistent logging throughout `api/bgg_api/`
  and your Dash callbacks for easier debugging.
* **`config.py`**: Make sure `config.py` is properly set up with `BGG_API_URL`,
  `BGG_API_TOKEN`, `DB_FILE`, and `DEBUG` for all environments.
* **Styling**: Apply consistent styling using `dash-mantine-components`
  themeing.

---

---

## Phase 6: Detail View User Experience (UX)

*(Goal: Improve the usability and navigation of the game detail modal.)*

* **Task 6.1: Reset Modal Scroll on Navigation**
    * **Status:** **PENDING**
    * **Description:** Ensure the modal content resets to the top when navigating between associated games.
    * **Action:** Update the modal rendering logic or use a client-side callback to reset scroll position whenever the `bgg_id` changes.
* **Task 6.2: Implement Navigation History (Back/Forward)**
    * **Status:** **PENDING**
    * **Description:** Allow users to navigate through the history of games viewed within the current modal session.
    * **Action:** Maintain a `dcc.Store` holding a stack of visited `bgg_id`s. Add "Back" and "Forward" buttons to the modal header that update the current `bgg_id` from the stack.
* **Task 6.3: Expandable Sections for Associated Games**
    * **Status:** **PENDING**
    * **Description:** Use accordions or tabs to group associated games by type (Expansions, Reimplementations, etc.).
    * **Action:** Replace the flat list of associated games with `dmc.Accordion`, allowing users to expand categories and save vertical space.
* **Task 6.4: Detail Modal Layout Reorganization**
    * **Status:** **PENDING**
    * **Description:** Move the "Associated Games" section to the bottom and prioritize core game info.
    * **Action:** Refactor the modal body to list description and stats first, moving the more voluminous associated games list to a secondary section or the bottom.
* **Task 6.5: External BGG Link**
    * **Status:** **PENDING**
    * **Description:** Provide a direct link to the game's page on BoardGameGeek.
    * **Action:** Add a `dmc.Anchor` or "View on BGG" button in the modal footer or header.
* **Task 6.6: Animate Collection Cards**
    * **Status:** **PENDING**
    * **Description:** Animate card interface when loading/filtering collection interface.

---

## Phase 7: Data Sync & Progress Tracking

*(Goal: Provide better feedback and control over BGG data synchronization.)*

* **Task 7.1: Collection-Level Refresh Button**
    * **Status:** **PENDING**
    * **Description:** Add a button to the main collection view to manually trigger a full BGG sync.
    * **Action:** Add a "Refresh Collection" button to the header/sidebar that triggers the `save_collection_data_to_db` background process.
* **Task 7.2: Game-Level Refresh Button**
    * **Status:** **PENDING**
    * **Description:** Add a button in the detail modal to refresh data for a specific game.
    * **Action:** Add a "Sync with BGG" button in the modal that triggers `save_game_details_to_db` for the current `bgg_id`.
* **Task 7.3: Visual Progress Tracking for Sync**
    * **Status:** **PENDING**
    * **Description:** Replace the generic loading overlay with a detailed progress bar during sync.
    * **Action:** Implement a background task status tracker (possibly using `dcc.Interval` and a status file/DB table) and display a `dmc.Progress` bar showing "X of Y games synced".
* **Task 7.4: Modal Transition Loading States**
    * **Status:** **PENDING**
    * **Description:** Show a clear loading indicator when fetching data for an associated game within the modal.
    * **Action:** Ensure `dmc.LoadingOverlay` covers the modal content during `bgg_id` transitions.

---

## Phase 8: Advanced Navigation & Filtering

*(Goal: Enhance discovery and visual customization of the collection.)*

* **Task 8.1: Collection Filtering & Search**
    * **Status:** **PENDING**
    * **Description:** Allow users to filter the collection by various game attributes.
    * **Action:** Add sidebar filters for:
        *   Number of players (min/max)
        *   Complexity (weight)
        *   Play time
        *   Categories/Mechanics (MultiSelect)
    *   Update the `update_grid` callback to apply these filters to the SQLModel query.
* **Task 8.2: Theme Customization (Dark/Light Mode)**
    * **Status:** **PENDING**
    * **Description:** Implement a theme toggle and refine the color palette.
    * **Action:** Use Mantine's `ColorSchemeProvider` to allow toggling between light and dark modes. Tweak the theme colors for a more premium look.
* **Task 8.3: BGG User Profile Link**
    * **Status:** **PENDING**
    * **Description:** Link to the user's full collection on BGG.
    * **Action:** Add a link in the header or sidebar: "View Collection on BoardGameGeek".

---

## Phase 9: Settings & Personalization

*(Goal: Manage user-specific data and improve visual indicators.)*

* **Task 9.1: Enhanced Ownership Badges**
    * **Status:** **PENDING**
    * **Description:** Add badges for "Wishlist", "Want to Play", and "Want to Buy" statuses.
    * **Action:** Map additional BGG collection flags to UI badges. Use distinct colors for each status.
* **Task 9.2: Badge Layout & Styling Refinement**
    * **Status:** **PENDING**
    * **Description:** Improve the placement and visibility of badges on game cards and list items.
    * **Action:** Reposition badges (e.g., to the left of the title or below) to prevent overflow in the associated games list. Explore using font styling (e.g., bolding) as an alternative indicator.
* **Task 9.3: Settings Configuration Page**
    * **Status:** **PENDING**
    * **Description:** Create a dedicated settings page for user configuration.
    * **Action:** Implement a page to manage:
        *   BGG Username
        *   Auto-sync frequency
        *   Preferred image quality/caching settings
