# Spielpendium: Feature Brainstorming & Future Roadmap

This document serves as a repository of ideas for future features,
enhancements, and architectural improvements for **Spielpendium**. These ideas
are categorized by theme to represent potential additions to the roadmap.

---

## 1. Game Night & Tabletop Companion

**Concept:** Tools and assistants designed to plan game nights, teach games,
and enrich the active tabletop play experience.

- **Group Recommendations & Planner:**
  - *Group Player Intersect:* Select multiple players (by BGG username or
    local profiles) to scan the intersection of collections and suggest
    commonly owned games.
  - *Smart Recommendations:* Filter suggestions by exact player count,
    "best at" player count (from BGG polls), play time limits, and
    complexity/weight.
  - *Randomizer ("What should we play?"):* A visual selector (like a
    spinning wheel) that suggests a random game matching active filters.
- **Host Assistant & "Teach the Game" Companion:**
  - *Setup Checklist:* Step-by-step setup guides, player aids, and direct
    links to official PDF rulebooks or embedded "Watch It Played" YouTube
    videos.
  - *Teach Scripts:* A structured outline to help hosts explain objectives,
    themes, and basic mechanics to new players quickly.
  - *Rules Quick-Reference:* A checklist of commonly forgotten rules and
    edge cases (e.g., hand limits, tie-breakers).
- **Active Tabletop Utilities:**
  - *Dynamic Digital Scorekeeper:* Point counters for simple games, and custom
    end-of-game score sheets for complex games (e.g. scoring categories for
    *7 Wonders* or *Wingspan*) that auto-sum and save scores directly to
    history.
  - *Turn Timer & Chess Clock:* Visual turn timers or chess clocks with gentle
    warnings to prevent analysis paralysis.
  - *Ambient Soundtrack & Lighting:* Links to themed music playlists (e.g.,
    cosmic synth for *Nemesis*) and smart lighting (e.g., Philips Hue)
    integration to set the game's color scheme in the room.
  - *Legacy & Campaign Tracker:* Save campaign states, player roles, and
    unlock checklists for legacy/campaign games.
  - *Smart Tabletop Tools:* A thematic "First Player Picker" (e.g., "who most
    recently visited a farm") and profiles to save player color preferences.
- **Active Hosting Utilities:**
  - *Clean Hands Snack Planner:* Suggest food/drink pairings matching the
    game's theme and categorize snacks by "grease/component risk" (e.g.,
    sleeved-card safe snacks).
  - *TV Casting / Spectator Mode:* A dedicated layout castable to a TV/tablet
    showing game status, turn order, active timers, scoreboards, or a rule Q&A
    feed.

---

## 2. Social & Sharing Features

**Concept:** Features that connect players, allow collections to be shared
with guests, and facilitate multiplayer collaboration.

- **Public Shareable Collections (Read-Only Guest Mode):**
  - *Dynamic Routing:* Generate shareable URLs (e.g., `/collection/<username>`
    or `/share/<username>`) utilizing Dash's multi-page routing.
  - *Guest Layout:* A read-only collection browser showing grids, search, and
    filters while hiding all database write options (like syncing or editing
    ratings).
- **Collection Comparison & Shared Shelves:**
  - *Overlap Dashboard:* Input a friend's BGG username to compare overlap
    (mutual games), uniqueness, and wishlist matching.
  - *Shared Shelf Space:* Combine multiple collections into a single virtual
    shelf for a regular playgroup (which could replace the current
    multi-username settings scheme).

---

## 3. Collection Analytics & Economics

**Concept:** In-depth statistics, performance graphs, play trends, and
financial tracking for your collection.

- **Play Tracking & Performance:**
  - *BGG Play Logs:* Import play histories and display win/loss rates, player
    counts, and favorite designers.
  - *Heatmaps & H-Index:* Visual calendar heatmap of plays (GitHub-style
    contribution grid) and calculation of the user's H-Index.
- **Inactivity & Ignored Games:**
  - *Shelf of Shame:* Highlight owned games with 0 logged plays.
  - *Inactivity Alerts:* A list of games that haven't been played in over 365
    days.
- **Board Game Economics (Cost-Per-Play):**
  - *ROI Calculator:* Log purchase prices or MSRPs to calculate
    cost-per-play ratios (e.g., a $60 game played 15 times costs $4.00 per
    play).
  - *Decluttering Assistant:* Flag low-ROI games to help users decide what to
    sell or trade.

---

## 4. Physical Organization & UI Enhancements

**Concept:** Visual improvements and tools to assist in the storage, labeling,
and spatial layout of physical board games.

- **Physical Shelf Space Planner:**
  - *Kallax Grid Optimizer:* Use box dimensions (width, height, depth) to
    drag-and-drop games into a virtual IKEA Kallax grid, checking space/weight
    limits and styling by color.
- **Custom Organization & UI Labels:**
  - *Virtual Boxes:* Create custom local labels (e.g., "Camping Games",
    "Selling Soon") to tag and filter games outside of standard categories.
  - *Interactive Shelf View:* Visual "3D shelf" or vertical book-spine
    rendering of the collection.
  - *BGG Poll Overlays:* Embed BGG poll metrics directly onto cards (e.g.
    language dependency, recommended player counts).

---

## 5. Exporting & Portability

**Concept:** Options to export collection data, print materials, and browse
your catalog without a live internet connection.

- **Compendium PDF Generator (The Original Vision):**
  - *Table of Contents:* Automatically compiled page index with clickable
    links.
  - *Game Family Grouping:* Sort games alphabetically, but keep expansions,
    promos, and spinoffs nested directly underneath the base game (e.g.,
    *Catan* followed by its expansions).
  - *Rich Layout Pages:* High-res cover art, weight/complexity, player
    statistics, and BGG description formatting.
  - *Layout Density Options:* Switch between a full-page compendium catalog
    and a compact, multi-column checklist.
- **Printable Assets & Offline Storage:**
  - *Shelf Tags & QR Codes:* Print QR codes to display on shelves that link
    directly to rulebooks or detail pages.
  - *Data Exports:* Export raw database records to CSV or JSON formats.
  - *Offline Image Pre-fetching:* Cache game cover images locally so the
    collection remains fully browsable when offline.
- **Progressive Web App (PWA) Support:**
  - *Mobile/Desktop Installation:* Configure a web app manifest and service
    workers to allow users to install Spielpendium directly onto their phone's
    home screen or computer desktop as a standalone app.
  - *Offline Accessibility:* Use caching strategies to serve the collection,
    filtered view, and locally downloaded game graphics even during a complete
    internet outage at a game night.

---

## 6. Third-Party API Integrations

**Concept:** Connect external services to enrich the data, ambiance, and
social reach of the platform.

- **Market & Price Tracking (BoardGamePrices API):**
  - Live retail pricing and stock checking mapped directly to your wishlist or
    owned games.
  - Automatically evaluate the replacement cost or secondary market value of
    the library.
- **Audio & Ambiance (Spotify API):**
  - Search public playlists for tracks matching a board game's specific theme
    and embed a Spotify web player on the game details page.
- **Digital Play & Virtual Tabletop (Steam Workshop & BGA):**
  - Query Tabletop Simulator (TTS) workshop mods to see if games in the
    collection are playable online.
  - Generate deep links to Board Game Arena (BGA) lobbies for instant online
    sessions.
- **Interactive Media (YouTube API):**
  - Embed rule tutorials (e.g. from channels like *Watch It Played* or *3
    Minute Board Games*) dynamically inside the detail views.
- **Rules Assistance (OpenAI / Anthropic Claude API):**
  - A chat assistant that references rulebooks to answer gameplay questions
    as a "digital rules referee" at the table.
- **Social Messaging (Discord / Telegram Webhooks):**
  - Push automated notifications to the playgroup's chat server for game
    night scheduling, new library additions, or score tracking milestones.
