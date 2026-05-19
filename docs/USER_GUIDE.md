# Spielpendium User Guide

Welcome to **Spielpendium**! This guide will help you connect your BoardGameGeek (BGG) account, filter and
search your collection, and customize the visual theme to build your ultimate digital board game parlor companion.

---

## 1. Connecting Your BoardGameGeek (BGG) Account

To view and manage your collection, you must connect your BGG profile. Spielpendium uses BGG's public XML API2
to fetch your games, play stats, and ownership statuses.

### How to Connect

1. Navigate to the **Home** page.
2. In the connection card, enter your exact **BoardGameGeek Username**.
3. Click **Connect Profile**.
4. Spielpendium will establish a connection to BGG.

> [!NOTE]
> **Understanding BGG API Queue Times**
> When fetching a collection for the first time, BGG's server queues the request and returns an HTTP `202 Accepted`
> status while it compiles the data. Spielpendium is built with rate-limit resilient retry handlers. The
> connection indicator will show a loading spinner while waiting for BGG. Do not refresh or close the page—the
> system will retrieve the collection automatically!

---

## 2. Managing & Ingesting Your Collection

Once connected, your collection is saved locally to your Spielpendium database so pages load instantly
without calling BGG again.

### Syncing Updates

Whenever you buy new games or update your BGG collection online, click **Refresh Database** at the top
right of the Collection page.

- A live progress indicator will show exactly how many games are being fetched and updated in real-time.
- Spielpendium fetches full metadata, game graphics, player counts, playtimes, ratings, and video reviews
  in background batches.

### Multi-User Support

Spielpendium supports managing multiple usernames!

- Go to **Settings** to add additional BGG usernames.
- You can switch between active user profiles instantly from the navigation sidebar or settings panel.

---

## 3. Advanced Filtering & Search

Spielpendium features an ultra-responsive, real-time filtering engine that makes it simple to pick the
perfect game for any game night.

### Text Search

Use the **Search Games** box to instantly filter games by title. It updates as you type!

### Core Filters

- **Ownership Badges**: Filter by your active status (Own, Previously Owned, Want to Play, Wishlist,
  For Trade, Want in Trade, Preordered, Want to Buy).
- **Player Count Matcher**: Select the exact number of players joining your session. The system will
  match games that explicitly support that count.
- **Play Time**: Use the range slider to select minimum and maximum playtimes in minutes.
- **BGG Rating**: Filter by the game's official BGG user rating (from 1 to 10).

---

## 4. Theme & Accent Customization

Spielpendium is built with a state-of-the-art Mantine-powered visual engine that looks beautiful in
any environment.

### Changing Layout View

You can toggle between two premium visual densities at the top right of the collection page:

1. **Grid View**: A beautiful card-based layout highlighting cover art, BGG ratings, and player details.
2. **List View**: A sleek, high-density table view perfect for large collections. It highlights cover
   art thumbnails, ratings, player counts, playtimes, and status badges in a compact tabular design.

### Theme & Accent Selection

Navigate to the **Settings** page to customize:

- **Visual Mode**: Switch between **Dark Mode** (sleek slate background) and **Light Mode** (clean
  glassmorphism layout).
- **Accent Color**: Choose your favorite premium accent color palette (e.g. Sapphire Blue, Forest Green,
  Vibrant Red, Majestic Violet, Crimson Orange, Warm Amber, Slate Gray) to customize all buttons, badges,
  sliders, and progress indicators instantly.
