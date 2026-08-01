# PRD — Disaster Response & Mutual Aid Information System

## SDLC role

This document owns **Planning** and **Requirements** phases. Full lifecycle map: [RFC.md — SDLC phase coverage](RFC.md#sdlc-phase-coverage).

| Phase | What this file provides |
|-------|-------------------------|
| **Planning** | Problem statement, constraints, non-goals, scope boundaries |
| **Requirements** | User stories, acceptance criteria, Given/When/Then scenarios (IDs for testing) |

## Problem

When disasters hit Indonesia, residents lack lightweight access to official hazard data and volunteers lack a single map to match needs with offers — especially when bandwidth is degraded and heavy apps fail.

## User Stories

### Story 1: Check weather in chat

As a **resident**, I want to check current weather for my area through a chat bot, so that I can prepare for floods or storms without installing a heavy mobile app.

**Acceptance criteria**

- [ ] I can open the bot and see a clear menu without typing commands from memory (W-01)
- [ ] I can share my GPS location or pick/search my area and receive a readable weather forecast (temperature, conditions, wind) (W-02, W-05, W-09, W-10)
- [ ] The answer appears in the same chat thread within a few seconds on a normal mobile connection (W-05)
- [ ] If weather data is unavailable, I see a short friendly message instead of a silent failure (W-06)
- [ ] If I type a region name that cannot be found, I get a clear message and can try again (W-03)
- [ ] If the region lookup service fails, I get a fallback message and am not left with a crashed bot (W-04)
- [ ] If weather data is malformed, I still see a readable message rather than an error screen (W-07)
- [ ] If GPS reverse-geocoding fails, I am prompted to type my location manually (W-11)

**Test scenarios**

| ID | Given | When | Then |
|----|-------|------|------|
| W-01 | User on main menu | Taps weather | Bot shows GPS or text input options |
| W-02 | User typed a valid province | Search completes | Kab/kota button list is shown |
| W-03 | User typed unknown text | Search runs | Friendly “not found” message; no crash |
| W-04 | Wilayah API fails | User searches | Fallback message; suggests `/start` |
| W-05 | User completes drill-down or GPS/text shortcut | Weather source returns data | Summary shows temperature, conditions, and wind |
| W-06 | User completes drill-down | Weather source returns nothing | Friendly outage message and back button |
| W-07 | Weather source returns malformed data | Format step runs | Format fallback text; no exception shown to user |
| W-08 | Village ID `3674060001` | Region code is converted for weather API | Correct administrative code is used (see RFC) |
| W-09 | User on weather entry | Sends GPS location | Reverse geocode + weather shown |
| W-10 | User types kecamatan name | smart_search matches district | Weather shown without drill-down buttons |
| W-11 | Nominatim fails or no Emsifa match | User sent GPS | Fallback prompt to type location manually |

### Story 2: See latest earthquake info

As a **resident**, I want to see the latest earthquake information in chat, so that I can quickly judge local impact and tsunami risk.

**Acceptance criteria**

- [ ] I can request earthquake info from the main menu in one tap (Q-01)
- [ ] The response includes magnitude, location description, time, and depth in plain language (Q-02)
- [ ] Tsunami potential (if provided by the source) is shown clearly (Q-02)
- [ ] If earthquake data is down, I still get a helpful fallback message (Q-03)
- [ ] If earthquake data is malformed, I still get a readable message (Q-04)

**Test scenarios**

| ID | Given | When | Then |
|----|-------|------|------|
| Q-01 | Main menu | User taps earthquake info | Latest earthquake is fetched and shown |
| Q-02 | Earthquake source OK | Response is parsed | Magnitude, location, time, depth, and tsunami potential are shown |
| Q-03 | Earthquake source down | User taps earthquake info | Fallback message with link to official source |
| Q-04 | Malformed earthquake JSON | Format step runs | Format fallback; no user-visible crash |

### Story 3: Report disaster or mutual aid

As a **resident**, I want to report a disaster, request help, or offer help with my location, so that neighbors and responders can see my situation on a shared map.

**Acceptance criteria**

- [ ] I can start a guided report flow from the main menu (R-01)
- [ ] I choose whether I need help, offer help, or share info only (R-01)
- [ ] I can type a short description and share my location from Telegram (R-02, R-03)
- [ ] I receive confirmation in chat after a successful submission (R-04)
- [ ] My report appears on the volunteer dashboard within about one minute (R-04, F-01)
- [ ] If I send text instead of location at the location step, I am prompted again (R-06)
- [ ] If saving fails, I see an error message and can try again later (R-05)
- [ ] I can cancel mid-flow with `/cancel` (R-07)
- [ ] For need-help and offer-help reports, my Telegram display name and username are saved automatically (R-08)
- [ ] Info-only reports do not store my contact details (R-09)

**Test scenarios**

| ID | Given | When | Then |
|----|-------|------|------|
| R-01 | Main menu | User taps report | Three report-type buttons are shown |
| R-02 | Report type chosen | User sends text description | Location share keyboard is shown |
| R-03 | Description saved | User shares location | Report is saved with latitude and longitude |
| R-04 | Database insert succeeds | Location received | Success confirmation in chat |
| R-05 | Database insert fails | Location received | Error message; location keyboard removed |
| R-06 | User in location step | User sends text not location | Flow stays on location step; reprompt for location |
| R-07 | User mid report flow | User sends `/cancel` | State cleared; cancel message shown |
| R-08 | NEED_HELP or OFFER_HELP report | User shares location | Report saved with `contact_name` and `telegram_username` snapshot |
| R-09 | INFO_ONLY report | User shares location | Report saved with null contact fields |

### Story 4: Multi-layer hazard map

As a **volunteer or NGO operator**, I want a map that overlays earthquakes, crowdsourced disaster reports, and mutual-aid pins, so that I can prioritize where to send limited resources.

**Acceptance criteria**

- [ ] I can open the dashboard in a browser without installing software (M-01)
- [ ] The map shows recent earthquake activity as a visible layer (M-02)
- [ ] The map shows recent crowdsourced disaster points (e.g. flood, wind) from open data (M-03)
- [ ] Mutual-aid reports appear as map markers (M-04)
- [ ] Need-help and offer-help reports are visually distinguishable (M-05)
- [ ] Bad coordinate data in one row does not break the whole map (M-06)

**Test scenarios**

| ID | Given | When | Then |
|----|-------|------|------|
| M-01 | Dashboard loads | Page opens in browser | Interactive map is rendered |
| M-02 | Quake list non-empty | Map is built | Red earthquake marker layer is present |
| M-03 | Crowdsourced disaster GeoJSON OK | Map is built | Blue disaster layer is present |
| M-04 | Mutual-aid rows exist | Map is built | Markers appear at report coordinates |
| M-05 | Mixed need-help and offer-help reports | Map is built | Need-help and offer-help use distinct marker colors |
| M-06 | One quake row has bad coordinates | Map is built | Bad row skipped; map still renders |

### Story 5: Filter report status

As a **volunteer or NGO operator**, I want to filter mutual-aid reports by status, so that I can focus on open cases and track what is already resolved.

**Acceptance criteria**

- [ ] I can filter by open, in progress, and resolved states (F-01)
- [ ] I can filter by report type (need help, offer help, info only) (F-01)
- [ ] Changing a filter updates the map and list without a manual full-page reload (F-02)
- [ ] My filter choice stays applied while I interact with the dashboard in one session (F-03)
- [ ] I can see reporter contact (name and Telegram link when available) in the report table and map popup (F-04)

**Test scenarios**

| ID | Given | When | Then |
|----|-------|------|------|
| F-01 | Reports with mixed statuses and types | Filter applied (e.g. OPEN only) | Map and table show only matching reports |
| F-02 | Dashboard open | User toggles filter | Map and table update on next interaction |
| F-03 | Active session | User interacts multiple times | Filter keys persist in session state |
| F-04 | NEED_HELP report with contact fields | Dashboard loads | Table and map popup show contact name; link if username exists |

### Story 6: Graceful degradation

As a **resident**, I want the bot to stay usable when external data sources fail, so that I can still report emergencies or read other information during partial outages.

**Acceptance criteria**

- [ ] A failed weather fetch does not crash the bot (G-01)
- [ ] A failed earthquake fetch does not crash the bot (G-02)
- [ ] Error messages explain what failed and suggest an alternative when possible (G-01, G-02)
- [ ] The report flow still works when hazard APIs are down, as long as the database is reachable (G-03)

**Test scenarios**

| ID | Given | When | Then |
|----|-------|------|------|
| G-01 | Weather source fails | User requests weather | Bot responds with fallback; no crash |
| G-02 | Earthquake source fails | User requests earthquake info | Fallback message shown |
| G-03 | Hazard APIs down, database up | User completes report flow | Report still saves successfully |

### Story 7: Dev and production deployment

As a **system operator**, I want the same bot features to run locally during the hackathon and on a hosted URL for demo, so that judges and users can try the product without my laptop online.

**Acceptance criteria**

- [ ] The bot runs locally for development without a public domain or SSL certificate (C-04)
- [ ] A production deployment path exists for a hosted webhook URL (C-04)
- [ ] Secrets are loaded from environment variables, not hardcoded in the repository (C-01, C-03)
- [ ] Missing required configuration fails fast at startup with a clear error (C-01)
- [ ] The bot application builds successfully when configuration is valid (C-02)

**Test scenarios**

| ID | Given | When | Then |
|----|-------|------|------|
| C-01 | Missing `TELEGRAM_BOT_TOKEN` (or other required env) | Startup validation runs | Error names the missing variable |
| C-02 | All required env vars set | Application is built | No build error |
| C-03 | Repository scanned | Search for hardcoded secrets | Only placeholders in `.env.example` |
| C-04 | Dev mode | Bot started locally | Polling works without `WEBHOOK_URL` |

## Cross-cutting test scenarios

### Retry utility (RT)

| ID | Given | When | Then |
|----|-------|------|------|
| RT-01 | Callable fails twice then succeeds | Retry wrapper runs | Returns result after three attempts |
| RT-02 | Callable always fails | Retry wrapper runs with max retries | Raises after retries exhausted |

### Wilayah lookup (L)

| ID | Given | When | Then |
|----|-------|------|------|
| L-01 | Exact name match in candidate list | Best match runs | Returns matching item |
| L-02 | Substring match only | Best match runs | Returns first substring match |
| L-03 | No match in list | Best match runs | Returns nothing |
| L-04 | Mixed-case input | Best match runs | Case-insensitive match works |
| L-05 | District has villages | resolve_adm4_for_bmkg runs | Returns BMKG adm4 from first village |
| L-06 | District has no villages | resolve_adm4_for_bmkg runs | Returns nothing |

## Scenario index (acceptance criteria → IDs)

| Story | Criteria map to |
|-------|-----------------|
| Story 1 | W-01–W-11 |
| Story 2 | Q-01–Q-04 |
| Story 3 | R-01–R-09 |
| Story 4 | M-01–M-06 |
| Story 5 | F-01–F-04 |
| Story 6 | G-01–G-03 |
| Story 7 | C-01–C-04 |

## Non-goals

**Not in this hackathon MVP**

- Native iOS or Android apps
- Full admin RBAC, audit logs, or multi-tenant organization accounts
- Automated push alerts or scheduled weather broadcasts to all subscribers
- Fuzzy matching of free-text city names to official region codes (implemented for kecamatan search + Nominatim GPS)
- NLP or LLM urgency scoring from citizen free-text reports
- WhatsApp Cloud API as a primary channel
- Paid SMS, satellite comms, or offline mesh networking
- Microservices or a custom REST backend beyond managed database APIs
- Production-grade SLA, 24/7 on-call, or penetration testing

**Post-hackathon roadmap (documented, not built now)**

- Migrate primary channel from Telegram to WhatsApp Cloud API for wider reach in Indonesia
- LLM-based extraction of urgency from reports and auto-prioritization on the dashboard
- Harden webhook-only production deployment on free-tier hosts

## Constraints

| Type | Constraint |
|------|------------|
| **Time** | ~4–5 hours build window; demo-ready on hackathon day |
| **People** | Solo or small team; Python-first skills assumed |
| **Cost** | Free-tier hosting: Render (bot), Streamlit Community Cloud (dashboard), Supabase (database) |
| **Data** | Open APIs only: BMKG, PetaBencana.id, static Indonesia administrative JSON; respect provider rate limits |
| **Legal / privacy** | No secrets in repo; store minimal identity (Telegram ID, report text, coordinates); no payments or medical records |
| **Network** | Must work on degraded mobile bandwidth; chat UI preferred over heavy web client for residents |
| **Platform** | Telegram Bot (residents) + web dashboard (volunteers); judges access dashboard via browser URL |
