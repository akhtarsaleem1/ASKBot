# ASKBot v2.0 — Premium Marketing Engine + Dashboard Upgrade

Complete overhaul of ASKBot's creative pipeline and dashboard with 9 new features across 4 phases.

## User Review Required

> [!IMPORTANT]
> This is a large upgrade touching ~20 files. I recommend we build it in **4 phases**, deploying each phase before starting the next. Each phase takes ~15-25 minutes. Please confirm you want all 4 phases, or pick which to start with.

> [!WARNING]  
> **Custom branding** requires you to provide a logo/watermark image file. Please place it at `d:\Software\ASKBot\data\assets\brand_logo.png` (PNG with transparency). If you don't have one, I'll skip the watermark feature.

## Open Questions

1. **Multi-app rotation**: Currently the bot picks 1 app per day. Do you want it to post about **multiple apps per day** (e.g. 2-3), or keep 1 per day but ensure it cycles through all apps evenly?
2. **Scheduling**: Do you want different post times per platform (e.g. LinkedIn at 9am, Twitter at 12pm), or just the ability to set multiple daily time slots?
3. **Engagement tracking**: Buffer's free plan has limited analytics API access. Should I build the tracking UI and gracefully handle cases where analytics data isn't available?

---

## Phase 1: Premium Image Design Engine
*Estimated: ~15 min — High Impact*

### Image Generator — ASK Prompts Style

#### [MODIFY] [image_generator.py](file:///d:/Software/ASKBot/askbot/services/image_generator.py)

Complete redesign of the layout system to produce **structured marketing graphics** like the ASK Prompts example:

- **LLM designs the entire layout concept** — not just the background prompt, but the layout structure, color palette, and visual concept
- **New layout templates** modeled after professional marketing graphics:
  - `_layout_feature_showcase` — Highlight a key feature with icon + description cards
  - `_layout_benefit_cards` — Two-column comparison cards (like the ASK Prompts "Bad vs Good" design)
  - `_layout_hero_spotlight` — Full-bleed hero with elegant text overlay
  - `_layout_phone_mockup` — Simulated phone frame showing the app concept
  - `_layout_stats_highlight` — Rating, installs, and key metrics displayed prominently
- **Custom branding**: Optional watermark/logo overlay on every image
- **Dynamic color palettes**: LLM picks harmonious colors per app category
- **No more dark-only backgrounds** — light, pastel, gradient, and dark themes

#### [MODIFY] [content.py](file:///d:/Software/ASKBot/askbot/services/content.py)

- Add **hashtag generation** to the LLM content prompt
- Return hashtags as part of `GeneratedContent`
- Platform-specific hashtag counts (Instagram: 15-20, Twitter: 3-5, LinkedIn: 3-5)

#### [MODIFY] [models.py](file:///d:/Software/ASKBot/askbot/models.py)

- Add `hashtags` field to `GeneratedPost`
- Add `ai_prompt_used` field to track what prompt was used (debugging + no-repeat)
- Add `layout_used` field to track which layout was applied

---

## Phase 2: Dashboard Upgrade — Gallery, Preview & History
*Estimated: ~20 min — High Impact*

### Manual Trigger with Preview

#### [MODIFY] [dashboard.py](file:///d:/Software/ASKBot/askbot/dashboard.py)

- **`GET /preview`** — Preview page: select an app, generate image + text, display it before posting
- **`POST /preview/generate`** — Generate preview (dry run, returns image + text)
- **`POST /preview/publish`** — Publish the previewed content to Buffer
- **`GET /gallery`** — Image gallery page showing all generated images with thumbnails
- **`GET /history`** — Post history feed with images, text, platform, and status
- **`GET /api/images/{filename}`** — Serve generated images from the assets directory

#### [NEW] [preview.html](file:///d:/Software/ASKBot/askbot/templates/preview.html)

- App selector dropdown
- "Generate Preview" button
- Live preview showing: generated image, post text per platform, hashtags
- "Publish to Buffer" button

#### [NEW] [gallery.html](file:///d:/Software/ASKBot/askbot/templates/gallery.html)

- Grid of generated image thumbnails
- Click to view full-size
- Shows app name, date, layout used
- Filter by app, date range

#### [NEW] [history.html](file:///d:/Software/ASKBot/askbot/templates/history.html)

- Card-based feed showing each post with:
  - Generated image thumbnail
  - Post text
  - Platform badge
  - Status (queued/published/rejected)
  - Date & time

#### [MODIFY] [base.html](file:///d:/Software/ASKBot/askbot/templates/base.html)

- Add nav links: Preview, Gallery, History
- Modernize CSS with better dark theme

#### [MODIFY] [styles.css](file:///d:/Software/ASKBot/askbot/static/styles.css)

- Image gallery grid styles
- Preview page layout
- History feed cards with image thumbnails

---

## Phase 3: Smart Rotation & Scheduling
*Estimated: ~15 min*

### Multi-App Daily Rotation

#### [MODIFY] [rotation.py](file:///d:/Software/ASKBot/askbot/services/rotation.py)

- Ensure every enabled app gets promoted before any app repeats
- Track promotion frequency per app
- Weighted rotation: newer or lower-performing apps get boosted

### Scheduling Control

#### [MODIFY] [scheduler.py](file:///d:/Software/ASKBot/askbot/scheduler.py)

- Support multiple daily time slots (e.g. "09:00,12:00,18:00")
- Each slot promotes a different app from the rotation queue

#### [MODIFY] [settings.html](file:///d:/Software/ASKBot/askbot/templates/settings.html)

- Add multi-time scheduling UI
- Show current schedule with visual timeline

#### [MODIFY] [settings_store.py](file:///d:/Software/ASKBot/askbot/services/settings_store.py)

- Add `SETTING_SCHEDULE_SLOTS` for multiple time slots

---

## Phase 4: Analytics & Engagement Tracking
*Estimated: ~15 min*

### Buffer Analytics Integration

#### [NEW] [analytics.py](file:///d:/Software/ASKBot/askbot/services/analytics.py)

- Pull post performance from Buffer API (impressions, clicks, engagement)
- Store metrics in local DB
- Calculate per-app and per-platform performance scores

#### [MODIFY] [models.py](file:///d:/Software/ASKBot/askbot/models.py)

- Add `PostMetrics` model (impressions, clicks, engagement_rate, fetched_at)

#### [NEW] [analytics.html](file:///d:/Software/ASKBot/askbot/templates/analytics.html)

- Dashboard with charts:
  - Posts per week
  - Top-performing apps
  - Best posting times
  - Platform comparison
- All rendered with lightweight vanilla JS charts (no external dependencies)

#### [MODIFY] [dashboard.py](file:///d:/Software/ASKBot/askbot/dashboard.py)

- Add `GET /analytics` route
- Add `POST /actions/fetch-analytics` to pull latest metrics

#### [MODIFY] [scheduler.py](file:///d:/Software/ASKBot/askbot/scheduler.py)

- Add weekly analytics fetch job

---

## Verification Plan

### Automated Tests
- Run `trigger_run.py` to verify end-to-end image generation with new layouts
- Verify server starts cleanly: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\restart.ps1`
- Hit each new dashboard route in the browser

### Manual Verification  
- Visually inspect generated images in the Gallery page
- Test Preview → Generate → Publish flow
- Confirm Buffer posts include hashtags
- Check rotation cycles through all apps
