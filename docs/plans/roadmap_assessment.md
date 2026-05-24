# Roadmap Feature Assessment & Feasibility Analysis

This document provides a comprehensive technical and strategic assessment of
the feature ideas proposed in
[feature_brainstorming.md](/Users/eddie/python_projects/spielpendium/docs/plans/feature_brainstorming.md).
It outlines implementation feasibility, value, risk, and mitigations.

---

## 1. Summary Feasibility Matrix

| Feature Theme | Difficulty | Value / ROI | Est. Time | Key Prerequisite |
| :--- | :--- | :--- | :--- | :--- |
| **1. Game Night** | Medium | High | 5-7 days | Session state, timers |
| **2. Social Share** | Medium | High | 3-4 days | Guest router, multi-db |
| **3. Analytics** | Low | Medium | 2-3 days | BGG Plays ingestion |
| **4. Kallax/UI** | High | Low | 6-8 days | Drag-drop Canvas |
| **5. PDF/Export** | Completed | High | -- | ReportLab / PWA manifest |
| **6. API Integr.** | Medium | Medium | 4-6 days | API access tokens |
| **7. Cloud Sync** | High | High | 5-7 days | Hosted Auth backend |

---

## 2. Detailed Feature Theme Evaluations

### Theme 1: Game Night & Tabletop Companion

- **Expected Difficulty:** Medium
  - Designing modular callbacks for timers and score sheets is straightforward,
    but client-side visual state synchronization (e.g., Turn Timers, TV Casting)
    adds complexity.
- **Value Added & ROI:** High
  - Directly expands Spielpendium from a static collection catalog into an
    active, utility-rich companion at the table.
- **Time to Implement:** 5-7 days
- **Prerequisites:**
  - Expanded `Game` model or separate `PlaySession`/`ScoreSheet` schema in
    [models.py](/Users/eddie/python_projects/spielpendium/util/models.py).
- **Risks & Mitigation:**
  - *Risk:* Turn timer latency or timer reset on page refresh.
  - *Mitigation:* Store active timer states in a server-side cache (e.g., local
    dictionary or cache wrapper) rather than relying purely on client-side JS.
- **Feature Creep Risks:** High
  - It is easy to spiral into building full digital board game simulators or
    comprehensive social organizers. Keep focus strictly on player helpers
    (timers, scorers, rules) and food planners simple.

---

### Theme 2: Social & Sharing Features

- **Expected Difficulty:** Medium
  - Multi-page routing is native in Dash, but separating private write
    endpoints from public read-only views requires strict layout partitioning.
- **Value Added & ROI:** High
  - Word-of-mouth growth. Users can share a single link with friends to show
    what they own or match player intersections.
- **Time to Implement:** 3-4 days
- **Prerequisites:**
  - Guest routing structure in [app.py](/Users/eddie/python_projects/spielpendium/app.py)
    and layout permissions.
- **Risks & Mitigation:**
  - *Risk:* Guest views accidentally triggering DB writes (syncing/refreshing).
  - *Mitigation:* Completely isolate the guest page layouts and skip all write
    actions at the layout generation level.
- **Feature Creep Risks:** Medium
  - Avoid building full social networks (chat, messaging, friends lists). Keep
    it to sharing and read-only collection overlaps.

---

### Theme 3: Collection Analytics & Economics

- **Expected Difficulty:** Low
  - We already have Plotly integration on the stats page; adding play logs and
    H-index calculations is math and query-based.
- **Value Added & ROI:** Medium
  - Appeals to statistics enthusiasts and collectors wanting to declutter or
    track cost-per-play metrics.
- **Time to Implement:** 2-3 days
- **Prerequisites:**
  - Ingestion functions for `/plays` endpoint in
    [client.py](/Users/eddie/python_projects/spielpendium/api/bgg_api/client.py)
    and a `PlayLog` SQLModel table in
    [models.py](/Users/eddie/python_projects/spielpendium/util/models.py).
- **Risks & Mitigation:**
  - *Risk:* Large collections fetching thousands of BGG play logs causing
    rate-limiting (HTTP 429).
  - *Mitigation:* Implement incremental, batched updates with exponential
    backoff.
- **Feature Creep Risks:** Low
  - Keep economics tracking to simple cost-per-play calculations, avoiding
    full inventory asset depreciation systems.

---

### Theme 4: Physical Organization & UI Enhancements

- **Expected Difficulty:** High
  - Custom drag-and-drop Kallax shelf visualization in Dash/Plotly or vanilla
    JS requires custom canvas code.
- **Value Added & ROI:** Low
  - A visual "cool factor," but low practical utility compared to planner
    tools or search engines.
- **Time to Implement:** 6-8 days
- **Prerequisites:**
  - Box dimension attributes (height, width, depth) in the `Game` table in
    [models.py](/Users/eddie/python_projects/spielpendium/util/models.py).
- **Risks & Mitigation:**
  - *Risk:* Missing box dimension data on BGG API (frequently unpopulated or
    wrong).
  - *Mitigation:* Allow manual dimensions entry and provide generic fallback
    sizes based on category/publisher.
- **Feature Creep Risks:** High
  - Writing complex custom layout algorithms. Limit the Kallax planner to a
    simple grid approximation rather than a full 3D physics shelf.

---

### Theme 5: Exporting & Portability (Completed)

- **Implementation Details:**
  - Implemented single-page-budget PDF catalog generation using ReportLab.
  - Features chronological grouping of franchise families via Connected
    Components (BFS), nested expansions, interactive Table of Contents, scaled
    typography, and official BGG branding compliance.
  - Generates catalogs in background worker threads with live status tracking.
- **Expected Difficulty:** Medium (Completed)
  - PDF generation was implemented with precise coordinate mapping and
    page-budget protection.
- **Value Added & ROI:** High
  - Realizes the "Compendium" aspect of the app's vision, giving users
    high-quality printouts.
- **Time to Implement:** 4-5 days (Completed in 4 days)
- **Prerequisites:**
  - Python `reportlab` library and service worker JS template in the `assets/`
    directory.
- **Risks & Mitigation:**
  - *Risk:* PDF rendering timeout or memory exhaustion with huge collections
    (500+ games).
  - *Mitigation:* Run PDF generation as a background task via a worker thread
    and cache the generated file.
- **Feature Creep Risks:** Low
  - Limit layout templates to 2-3 fixed options (compact checklist vs. full
    catalog) rather than custom layout builders.

---

### Theme 6: Third-Party API Integrations

- **Expected Difficulty:** Medium
  - Integrating multiple external APIs (Spotify, Steam, YouTube) requires
    setting up clients, managing auth, and handling failures.
- **Value Added & ROI:** Medium
  - Combines various media elements but relies heavily on third-party service
    stability.
- **Time to Implement:** 4-6 days
- **Prerequisites:**
  - API developer credentials for Spotify, YouTube, Steam, and OpenAI/Claude.
- **Risks & Mitigation:**
  - *Risk:* API key exhaustion (pricing) or sudden deprecations (e.g., OpenAI
    pricing, YouTube limits).
  - *Mitigation:* Graceful degradation. If Spotify/OpenAI is down, hide the UI
    element and fall back to standard local text layouts.
- **Feature Creep Risks:** High
  - The rules chatbot (AI) can grow into an expensive, open-ended support
    assistant. Set hard token limits per session.

---

### Theme 7: Authentication & Cloud Synchronization

- **Expected Difficulty:** High
  - Requires designing secure session storage, redirects, token encryption, and
    multi-user schema partitions.
- **Value Added & ROI:** High
  - Enables true cloud portability and data durability across devices.
- **Time to Implement:** 5-7 days
- **Prerequisites:**
  - Managed auth provider account (e.g., Clerk, Supabase, Auth0).
- **Risks & Mitigation:**
  - *Risk:* Exposing user data, session hacking, or complex schema migrations.
  - *Mitigation:* Use hosted backend auth (Clerk/Supabase) to outsource risk
    entirely. Never store raw passwords locally.
- **Feature Creep Risks:** Medium
  - Avoid custom user profile pages, friend requests, or team permissions. Keep
    authentication strictly to "Log In to Sync Database."
