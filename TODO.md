# 🗺️ WikiPhotoFinder: Web Application Roadmap & TODO

> **Vision:** Transform WikiPhotoFinder from a CLI tool into an all-in-one, community-wide Web Application hosted on **Wikimedia Toolforge (Wiki Cloud)**, empowering contributors across any language Wikipedia to visually discover, review, and add missing images from English Wikipedia / Commons with Wikipedia SSO and a 1-click split-screen review interface.

---

## 🎯 Target Architecture & User Flow

```
+-----------------------------------------------------------------------------------+
|  WikiPhotoFinder Web                                  [ 👤 Logged in as: User ]   |
+-----------------------------------------------------------------------------------+
|  Source Wiki: [ en.wikipedia.org ▼ ]   Target Wiki: [ ta.wikipedia.org ▼ ]         |
|  Category: [ Category:Living people              ]  Depth: [ 1 ▼ ]  [ 🔍 Start ]   |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|         LEFT PANE (Image & Metadata)          |     RIGHT PANE (Wikitext Diff)    |
|                                               |                                   |
|   +---------------------------------------+   |   Article: [[அட்லீ]] (Atlee)      |
|   |                                       |   |                                   |
|   |          [ Image Preview ]            |   |   @@ -2,4 +2,5 @@                 |
|   |        Atlee in 2013.jpg              |   |    {{Infobox person               |
|   |                                       |   |   - | image   =                   |
|   |   License: CC BY-SA 4.0 (Commons)     |   |   + | image   = Atlee in 2013.jpg |
|   |   Author: Silverscreen.in             |   |     | caption = 2014 விஜய்...    |
|   |   Dimensions: 1200 x 800              |   |                                   |
|   +---------------------------------------+   |   [✓] Also add to Wikidata (P18)  |
|                                               |                                   |
|   [ 🔗 View Commons File ] [ 🔗 enwiki Source ]|   [ ❌ Skip ]     [ ✅ Approve & Next ] |
|                                                                                   |
+-----------------------------------------------------------------------------------+
|  Queue: Article 14 of 86 (42 approved, 5 skipped)           [ ⏸ Pause / Export ]  |
+-----------------------------------------------------------------------------------+
```

---

## 📋 Task Breakdown & Milestones

### Phase 1: Authentication & Wikimedia Identity (SSO)
- [ ] **Wikimedia OAuth 2.0 Registration:**
  - [ ] Register new OAuth 2.0 client on [Wikimedia Meta-Wiki](https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration/propose).
  - [ ] Request required permissions: Basic identity (`oauth-identity`), edit pages (`edit`), and create claims on Wikidata (`editwikidata`).
  - [ ] Configure redirect URIs for local dev (`http://localhost:8000/callback`) and production Toolforge (`https://wikiphotofinder.toolforge.org/callback`).
- [ ] **Authentication Backend:**
  - [ ] Implement OAuth 2.0 authorization code flow with PKCE.
  - [ ] Secure HTTP-only session cookie management (JWT or encrypted session storage).
  - [ ] Fetch and display logged-in username, edit count, and global wiki groups.
  - [ ] Perform all edits explicitly under the authenticated user's account (preserving user accountability and contribution history).

---

### Phase 2: Web API & Backend Core
- [ ] **Framework Selection:**
  - [ ] Lightweight, high-performance Python framework (FastAPI or Flask) to seamlessly reuse existing `wiki_photos/` business logic.
- [ ] **Backend Services Integration:**
  - [ ] **Category Crawler Service:** Adapt `WikiPhotoFinder.find_missing_photos()` to stream results asynchronously via Server-Sent Events (SSE) or WebSockets.
  - [ ] **Diff Generation Engine:** Expose endpoints that generate HTML/colored wikitext diffs for any given article and proposed image insertion.
  - [ ] **Cross-Wiki Publishing Service:** Adapt `WikiUpdater.update_article()` to accept user OAuth tokens and commit changes directly to target wikis.
  - [ ] **Wikidata P18 Dispatcher:** Optional 1-click claim creation on Wikidata (`wbcreateclaim`) via user OAuth.
- [ ] **Queue & State Manager:**
  - [ ] Session-based review queues: Store pending candidates, approved edits, and skipped articles (in SQLite/Redis or browser session state).
  - [ ] Resumable queue support (save review session IDs).

---

### Phase 3: Split-Screen Review Frontend
- [ ] **Modern, Responsive Split-Screen UI:**
  - [ ] **Left Side (Media Showcase):**
    - High-resolution image preview with thumbnail fallback.
    - Freely-licensed Commons validation badge (CC-BY-SA, Public Domain, etc.).
    - Direct links to Wikimedia Commons file page and English Wikipedia source article.
    - Optional caption and author attribution preview.
  - [ ] **Right Side (Wikitext Diff Review):**
    - Clean visual side-by-side or inline diff showing exact proposed template modification.
    - Editable fields: Allow user to tweak image filename, custom caption, or alignment before approving.
  - [ ] **Action Bar:**
    - Primary green `[ ✅ Approve & Publish ]` button (hotkey: `Enter` or `A`).
    - Secondary `[ ⏭ Skip ]` button (hotkey: `S` or `Right Arrow`).
    - Optional toggle: `[✓] Add to Wikidata P18`.
    - Real-time progress bar (e.g. `12 / 85 articles processed`).
- [ ] **Fluid Single-Page Interaction:**
  - [ ] Fast, zero-reload transitions between queue items (using HTMX, Vue, or React).
  - [ ] Keyboard navigation shortcuts for power contributors.

---

### Phase 4: Universal Multi-Wiki Support & Localization
- [ ] **Any-to-Any Wiki Configuration:**
  - [ ] Language selector for **Source Wiki** (default: `en`, but supports `de`, `fr`, `Commons`, etc.).
  - [ ] Language selector for **Target Wiki** (Indic wikis: `ta`, `ml`, `te`, `kn`, `hi`, `bn`, `mr`; global wikis: `es`, `ar`, `ja`, etc.).
  - [ ] Auto-detect language-specific template parameters (`| படம் = `, `| చిత్రం = `, `| ചിത്രം = `, `| चित्र = `, `| image = `) and namespace prefixes (`[[படிமம்:...]]`, `[[പ്രமாணம்:...]]`, `[[దస్త్రం:...]]`).
- [ ] **UI Internationalization (i18n):**
  - [ ] Translate UI strings into Tamil, Hindi, Malayalam, Telugu, English, etc.
  - [ ] Integrate with [Translatewiki.net](https://translatewiki.net) standards or JSON i18n bundles.

---

### Phase 5: Wikimedia Toolforge Deployment (Wiki Cloud)
- [ ] **Toolforge Project Setup:**
  - [ ] Register new tool on Wikimedia Toolforge (`wikiphotofinder` or `wikiphotos`).
  - [ ] Configure Toolforge Python webservice (`webservice --backend=kubernetes python3.11 start`).
  - [ ] Secure environment variables for OAuth credentials (`client_id`, `client_secret`).
- [ ] **Wikimedia Etiquette & Rate Limiting:**
  - [ ] Transparent User-Agent header identifying Toolforge tool and authenticated editor:
    ```text
    WikiPhotoFinder-Web/2.0 (https://wikiphotofinder.toolforge.org; Toolforge; User:<username>)
    ```
  - [ ] Respect `maxlag=5` server backoff and concurrent user pacing on Toolforge Kubernetes cluster.
- [ ] **Automated Deployment & Health Monitoring:**
  - [ ] GitHub Actions workflow to deploy updates directly to Toolforge via SSH.
  - [ ] Uptime monitoring and error logging.

---

## 📅 Roadmap Schedule (Next Steps)

| Week / Sprint | Focus Area | Deliverables |
|---|---|---|
| **Week 1** | Architecture & OAuth Setup | Meta-Wiki OAuth registration, local FastAPI/Flask prototype, OAuth login demo. |
| **Week 2** | Backend API & Queue Engine | API endpoints for category scanning, candidate generation, and diff building. |
| **Week 3** | Split-Screen Frontend | Interactive UI with left-side image preview, right-side diff, and 1-click approve. |
| **Week 4** | Toolforge Deployment | Kubernetes deployment on `toolforge.org`, SSL, and multi-language wiki testing. |
| **Week 5** | Community Testing & Launch | Announce on Wikimedia Village Pumps (Tamil, Indic, global) for community feedback. |
