# BGG XML API — Integration Guide

Spielpendium uses the [BoardGameGeek XML API v2](https://boardgamegeek.com/wiki/page/BGG_XML_API2)
to fetch game data and user collections.

---

## API Token Requirement

BGG now **requires an Application Token** for all XML API requests. Without a
valid token, requests will be rejected.

### Getting a Token

1. Log in to BoardGameGeek.
2. Go to [https://boardgamegeek.com/applications](https://boardgamegeek.com/applications).
3. Register your application (provide a name and description).
4. Once registered, go to the **Tokens** tab within your application and
   generate a token.

### Using the Token

Send the token as a `Bearer` token in the `Authorization` request header:

```
Authorization: Bearer <your-token>
```

In Spielpendium, this is handled automatically in the `api/bgg_api/`
package via `get_xml_info()` in `client.py`. Set your token in the `.env` file:

```ini
BGG_API_TOKEN=your_token_here
```

> **Important:** Always request from `boardgamegeek.com`, **not**
> `www.boardgamegeek.com`. The `www` subdomain can interfere with
> Authorization headers.

> **Note:** Image assets are served from BGG's CDN (e.g.,
> `cf.geekdo-images.com`), which is a different domain than the API itself.
> The `get_single_image()` function intentionally omits the `Authorization`
> header for these requests.

---

## Rate Limiting

BGG throttles API traffic. In practice:

- A **5-second delay** between requests is recommended.
- A **202 response** means BGG is generating the data — wait and retry.
- A **429 response** means you are rate limited — wait longer and retry.
- **500 / 503 responses** also indicate throttling under heavy load.

Spielpendium handles all of these automatically in `get_xml_info()` using the
`MAX_API_CHECKS` and `TIME_BETWEEN_API_CHECKS` config settings.

---

## Terms of Use

The full terms are at
[boardgamegeek.com/wiki/page/XML_API_Terms_of_Use](https://boardgamegeek.com/wiki/page/XML_API_Terms_of_Use).
Key points:

| Requirement | Detail |
|---|---|
| **Attribution** | Must credit BoardGameGeek by name and display the "Powered by BGG" logo in any public-facing application |
| **Non-commercial** | API use is for non-commercial purposes only unless BGG grants explicit permission |
| **No AI/LLM training** | Using BGG data to train AI or LLM systems is strictly prohibited |
| **Mass data** | For bulk data (all game names, ranks, etc.), use BGG's [CSV data dumps](https://boardgamegeek.com/data_dumps/bg_ranks) instead of the API |

---

## Key Endpoints Used

| Endpoint | Purpose |
|---|---|
| `/xmlapi2/collection?username=…&stats=1` | Fetch a user's game collection with ownership status |
| `/xmlapi2/thing?id=…&stats=1` | Fetch detailed info for one or more games (up to 20 per request) |
| `/xmlapi2/search?query=…` | Search BGG by game title |

All endpoints return XML, which Spielpendium parses using `xmltodict`.

---

## Further Reading

- [Using the BGG XML API](https://boardgamegeek.com/using_the_xml_api)
- [BGG XML API v2 Reference](https://boardgamegeek.com/wiki/page/BGG_XML_API2)
- [XML API Terms of Use](https://boardgamegeek.com/wiki/page/XML_API_Terms_of_Use)
- [Register an Application / Get a Token](https://boardgamegeek.com/applications)
