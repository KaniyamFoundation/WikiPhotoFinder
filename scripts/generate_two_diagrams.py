#!/usr/bin/env python3
"""Generates two separate, beautiful SVG and Retina PNG flowcharts:
1. docs/find_photos_flow.svg & .png (Discovery phase)
2. docs/update_wiki_flow.svg & .png (Publishing phase)

Ensures all Unicode/Tamil/Indic text renders properly with no square boxes.
"""

import os
import cairosvg

FONT_STACK = "'Nirmala UI', 'FreeSans', 'Noto Sans Tamil', 'Noto Sans Malayalam', 'Noto Sans Telugu', 'Noto Sans Kannada', 'Noto Sans Devanagari', 'Noto Sans Bengali', 'DejaVu Sans', 'Liberation Sans', sans-serif"

# ==========================================
# 1. FIND PHOTOS FLOWCHART (find_missing_photos.py)
# ==========================================
FIND_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 1200" width="920" height="1200" style="background-color: #f8fafc; font-family: {FONT_STACK};">
  <defs>
    <filter id="shadow" x="-5%" y="-3%" width="110%" height="110%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0f172a" flood-opacity="0.06" />
      <feDropShadow dx="0" dy="1" stdDeviation="2" flood-color="#0f172a" flood-opacity="0.04" />
    </filter>

    <linearGradient id="headerGradFind" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#1d4ed8" />
      <stop offset="100%" stop-color="#3b82f6" />
    </linearGradient>

    <linearGradient id="cardGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" />
      <stop offset="100%" stop-color="#f8fafc" />
    </linearGradient>

    <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#3b82f6" />
    </marker>
    <marker id="arrowGray" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#94a3b8" />
    </marker>
  </defs>

  <!-- Canvas Background -->
  <rect width="920" height="1200" fill="#f8fafc" />

  <!-- Outer Border Container -->
  <rect x="20" y="20" width="880" height="1160" rx="20" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadow)" />

  <!-- Header Banner -->
  <g transform="translate(20, 20)">
    <path d="M 0 20 Q 0 0 20 0 L 860 0 Q 880 0 880 20 L 880 90 L 0 90 Z" fill="url(#headerGradFind)" />
    
    <!-- Top Badge -->
    <rect x="28" y="16" width="160" height="22" rx="11" fill="#ffffff" fill-opacity="0.2" />
    <text x="108" y="31" text-anchor="middle" fill="#ffffff" font-size="11" font-weight="700" letter-spacing="0.8">PART 1: DISCOVERY</text>

    <text x="28" y="62" fill="#ffffff" font-size="22" font-weight="800">Finding Missing Photos Workflow</text>
    <text x="28" y="80" fill="#bfdbfe" font-size="12">find_missing_photos.py • Category crawl, Commons verification, and multi-wiki sibling discovery</text>
  </g>

  <!-- STEP 1: Category Input -->
  <g transform="translate(50, 135)">
    <rect width="820" height="125" rx="14" fill="url(#cardGrad)" stroke="#cbd5e1" stroke-width="1.2" filter="url(#shadow)" />
    
    <rect x="20" y="16" width="65" height="22" rx="11" fill="#eff6ff" />
    <text x="52" y="31" text-anchor="middle" fill="#2563eb" font-size="11" font-weight="800">STEP 01</text>
    <text x="96" y="32" fill="#0f172a" font-size="16" font-weight="700">Target Wikipedia Category Input</text>
    <text x="20" y="60" fill="#475569" font-size="13">Provide any category in Tamil or English to inspect for missing photos:</text>

    <!-- Category Pill 1 -->
    <g transform="translate(20, 75)">
      <rect width="250" height="32" rx="8" fill="#f1f5f9" stroke="#cbd5e1" />
      <circle cx="18" cy="16" r="6" fill="#3b82f6" />
      <text x="32" y="21" fill="#0f172a" font-family="'Nirmala UI', 'Noto Sans Tamil', 'Lohit Tamil', sans-serif" font-size="12" font-weight="600">பகுப்பு:வாழும்_மக்கள்</text>
    </g>

    <!-- Category Pill 2 -->
    <g transform="translate(285, 75)">
      <rect width="260" height="32" rx="8" fill="#f1f5f9" stroke="#cbd5e1" />
      <circle cx="18" cy="16" r="6" fill="#3b82f6" />
      <text x="32" y="21" fill="#0f172a" font-size="12" font-weight="600">Category:Tamil film actors</text>
    </g>

    <!-- Depth Flag -->
    <g transform="translate(560, 75)">
      <rect width="240" height="32" rx="8" fill="#eff6ff" stroke="#bfdbfe" />
      <text x="120" y="21" text-anchor="middle" fill="#1e40af" font-size="12" font-weight="600">Subcategory depth: --depth 1</text>
    </g>
  </g>

  <!-- Connector 1 -> 2 -->
  <path d="M 460 260 L 460 285" stroke="#3b82f6" stroke-width="2.5" marker-end="url(#arrow)" fill="none" />

  <!-- STEP 2: Category Crawler -->
  <g transform="translate(50, 290)">
    <rect width="820" height="120" rx="14" fill="url(#cardGrad)" stroke="#cbd5e1" stroke-width="1.2" filter="url(#shadow)" />
    
    <rect x="20" y="16" width="65" height="22" rx="11" fill="#eff6ff" />
    <text x="52" y="31" text-anchor="middle" fill="#2563eb" font-size="11" font-weight="800">STEP 02</text>
    <text x="96" y="32" fill="#0f172a" font-size="16" font-weight="700">Category Crawl &amp; Polite Wikimedia Etiquette</text>
    <text x="20" y="60" fill="#475569" font-size="13">Batches API requests via HTTP POST to avoid URL length limits with multi-byte titles:</text>

    <!-- Etiquette Badges -->
    <g transform="translate(20, 75)">
      <rect width="220" height="30" rx="6" fill="#eff6ff" stroke="#bfdbfe" />
      <circle cx="16" cy="15" r="4" fill="#2563eb" />
      <text x="28" y="20" fill="#1e40af" font-size="12" font-weight="600">Polite delay: 1.0s (--delay)</text>

      <rect x="235" y="0" width="260" height="30" rx="6" fill="#eff6ff" stroke="#bfdbfe" />
      <circle cx="251" cy="15" r="4" fill="#2563eb" />
      <text x="263" y="20" fill="#1e40af" font-size="12" font-weight="600">Server load backoff: maxlag=5</text>

      <rect x="510" y="0" width="290" height="30" rx="6" fill="#eff6ff" stroke="#bfdbfe" />
      <circle cx="526" cy="15" r="4" fill="#2563eb" />
      <text x="538" y="20" fill="#1e40af" font-size="12" font-weight="600">HTTP 429/503 Exponential Backoff</text>
    </g>
  </g>

  <!-- Connector 2 -> 3 -->
  <path d="M 460 410 L 460 435" stroke="#3b82f6" stroke-width="2.5" marker-end="url(#arrow)" fill="none" />

  <!-- STEP 3: Photo Audit & Counterpart Match -->
  <g transform="translate(50, 440)">
    <rect width="820" height="135" rx="14" fill="url(#cardGrad)" stroke="#cbd5e1" stroke-width="1.2" filter="url(#shadow)" />
    
    <rect x="20" y="16" width="65" height="22" rx="11" fill="#eff6ff" />
    <text x="52" y="31" text-anchor="middle" fill="#2563eb" font-size="11" font-weight="800">STEP 03</text>
    <text x="96" y="32" fill="#0f172a" font-size="16" font-weight="700">Photo Audit &amp; English Article Match</text>
    
    <text x="20" y="60" fill="#475569" font-size="13">1. Inspects Tamil article: confirms it lacks a photo in infobox and lead wikitext.</text>
    <text x="20" y="80" fill="#475569" font-size="13">2. Follows Wikidata / langlinks: resolves the corresponding English Wikipedia article.</text>
    <text x="20" y="100" fill="#475569" font-size="13">3. Checks English article: verifies that an image is present (ignoring silhouettes &amp; stub icons).</text>

    <!-- Filter Badge -->
    <rect x="570" y="14" width="230" height="26" rx="6" fill="#f1f5f9" stroke="#e2e8f0" />
    <text x="685" y="31" text-anchor="middle" fill="#64748b" font-size="11" font-weight="600">Filters generic placeholders</text>
  </g>

  <!-- Connector 3 -> 4 -->
  <path d="M 460 575 L 460 600" stroke="#3b82f6" stroke-width="2.5" marker-end="url(#arrow)" fill="none" />

  <!-- STEP 4: Commons License Check -->
  <g transform="translate(50, 605)">
    <rect width="820" height="150" rx="14" fill="url(#cardGrad)" stroke="#cbd5e1" stroke-width="1.2" filter="url(#shadow)" />
    
    <rect x="20" y="16" width="65" height="22" rx="11" fill="#eff6ff" />
    <text x="52" y="31" text-anchor="middle" fill="#2563eb" font-size="11" font-weight="800">STEP 04</text>
    <text x="96" y="32" fill="#0f172a" font-size="16" font-weight="700">Wikimedia Commons Repository Verification</text>
    <text x="20" y="60" fill="#475569" font-size="13">Queries Commons API repository status to distinguish free photos from US Fair Use:</text>

    <!-- Commons Free Box -->
    <g transform="translate(20, 75)">
      <rect width="380" height="60" rx="8" fill="#ecfdf5" stroke="#a7f3d0" stroke-width="1.5" />
      <circle cx="20" cy="20" r="8" fill="#10b981" />
      <!-- White Checkmark -->
      <path d="M 16 20 L 19 23 L 25 17" stroke="#ffffff" stroke-width="2" fill="none" />
      <text x="36" y="24" fill="#065f46" font-size="13" font-weight="700">Hosted on Wikimedia Commons</text>
      <text x="36" y="44" fill="#047857" font-size="11">Freely licensed (CC-BY-SA / Public Domain). Ready to use!</text>
    </g>

    <!-- Local enwiki Box -->
    <g transform="translate(420, 75)">
      <rect width="380" height="60" rx="8" fill="#fffbeb" stroke="#fde68a" stroke-width="1.5" />
      <circle cx="20" cy="20" r="8" fill="#f59e0b" />
      <!-- Exclamation Mark -->
      <text x="20" y="25" text-anchor="middle" fill="#ffffff" font-size="12" font-weight="900">!</text>
      <text x="36" y="24" fill="#92400e" font-size="13" font-weight="700">Local English Wikipedia Only</text>
      <text x="36" y="44" fill="#b45309" font-size="11">US Fair Use only. Flagged for transfer before cross-wiki use.</text>
    </g>
  </g>

  <!-- Connector 4 -> 5 -->
  <path d="M 460 755 L 460 780" stroke="#3b82f6" stroke-width="2.5" marker-end="url(#arrow)" fill="none" />

  <!-- STEP 5: Multi-Language Sibling Exploration -->
  <g transform="translate(50, 785)">
    <rect width="820" height="155" rx="14" fill="url(#cardGrad)" stroke="#cbd5e1" stroke-width="1.2" filter="url(#shadow)" />
    
    <rect x="20" y="16" width="65" height="22" rx="11" fill="#eff6ff" />
    <text x="52" y="31" text-anchor="middle" fill="#2563eb" font-size="11" font-weight="800">STEP 05</text>
    <text x="96" y="32" fill="#0f172a" font-size="16" font-weight="700">Multi-Language Sibling Wiki Exploration</text>
    <text x="20" y="60" fill="#475569" font-size="13">Follows Wikidata sitelinks to discover other language editions lacking this exact photo:</text>

    <!-- Language Chips -->
    <g transform="translate(20, 75)">
      <rect width="115" height="30" rx="6" fill="#f1f5f9" stroke="#cbd5e1" />
      <text x="57" y="20" text-anchor="middle" fill="#334155" font-size="11" font-weight="600">ml (Malayalam)</text>

      <rect x="125" y="0" width="105" height="30" rx="6" fill="#f1f5f9" stroke="#cbd5e1" />
      <text x="177" y="20" text-anchor="middle" fill="#334155" font-size="11" font-weight="600">te (Telugu)</text>

      <rect x="240" y="0" width="110" height="30" rx="6" fill="#f1f5f9" stroke="#cbd5e1" />
      <text x="295" y="20" text-anchor="middle" fill="#334155" font-size="11" font-weight="600">kn (Kannada)</text>

      <rect x="360" y="0" width="95" height="30" rx="6" fill="#f1f5f9" stroke="#cbd5e1" />
      <text x="407" y="20" text-anchor="middle" fill="#334155" font-size="11" font-weight="600">hi (Hindi)</text>

      <rect x="465" y="0" width="105" height="30" rx="6" fill="#f1f5f9" stroke="#cbd5e1" />
      <text x="517" y="20" text-anchor="middle" fill="#334155" font-size="11" font-weight="600">bn (Bengali)</text>

      <rect x="580" y="0" width="105" height="30" rx="6" fill="#f1f5f9" stroke="#cbd5e1" />
      <text x="632" y="20" text-anchor="middle" fill="#334155" font-size="11" font-weight="600">mr (Marathi)</text>

      <rect x="695" y="0" width="85" height="30" rx="6" fill="#f1f5f9" stroke="#cbd5e1" />
      <text x="737" y="20" text-anchor="middle" fill="#334155" font-size="11" font-weight="600">pa / ur...</text>
    </g>

    <text x="20" y="132" fill="#16a34a" font-size="12" font-weight="600">Discovers opportunities to update multiple language projects simultaneously!</text>
  </g>

  <!-- Connector 5 -> Outputs -->
  <path d="M 460 940 L 460 965" stroke="#3b82f6" stroke-width="2.5" marker-end="url(#arrow)" fill="none" />

  <!-- STEP 6: Multi-Format Outputs -->
  <g transform="translate(50, 970)">
    <rect width="820" height="170" rx="14" fill="#eff6ff" stroke="#3b82f6" stroke-width="2" />
    
    <text x="20" y="32" fill="#1e40af" font-size="15" font-weight="800">STAGE 1 DELIVERABLES: MULTI-FORMAT EXPORTS</text>
    <text x="20" y="54" fill="#475569" font-size="13">Saves article candidates with full image metadata, Commons URLs, and wikitext snippets:</text>

    <!-- Output Cards Grid -->
    <g transform="translate(20, 72)">
      <rect width="180" height="75" rx="8" fill="#ffffff" stroke="#bfdbfe" />
      <text x="16" y="28" fill="#1e40af" font-size="14" font-weight="700">results.json</text>
      <text x="16" y="48" fill="#64748b" font-size="11">Structured data feed for</text>
      <text x="16" y="64" fill="#2563eb" font-size="11" font-weight="600">update_wiki.py</text>

      <rect x="195" y="0" width="180" height="75" rx="8" fill="#ffffff" stroke="#bfdbfe" />
      <text x="211" y="28" fill="#1e40af" font-size="14" font-weight="700">report.html</text>
      <text x="211" y="48" fill="#64748b" font-size="11">Interactive dashboard with</text>
      <text x="211" y="64" fill="#2563eb" font-size="11" font-weight="600">thumbnails &amp; copy buttons</text>

      <rect x="390" y="0" width="180" height="75" rx="8" fill="#ffffff" stroke="#bfdbfe" />
      <text x="406" y="28" fill="#1e40af" font-size="14" font-weight="700">report.md</text>
      <text x="406" y="48" fill="#64748b" font-size="11">GitHub-friendly tables</text>
      <text x="406" y="64" fill="#2563eb" font-size="11" font-weight="600">with clickable links</text>

      <rect x="585" y="0" width="195" height="75" rx="8" fill="#ffffff" stroke="#bfdbfe" />
      <text x="601" y="28" fill="#1e40af" font-size="14" font-weight="700">report.csv</text>
      <text x="601" y="48" fill="#64748b" font-size="11">Spreadsheet for team</text>
      <text x="601" y="64" fill="#2563eb" font-size="11" font-weight="600">tracking &amp; reporting</text>
    </g>
  </g>
</svg>"""


# ==========================================
# 2. UPDATE WIKI FLOWCHART (update_wiki.py)
# ==========================================
UPDATE_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 1320" width="920" height="1320" style="background-color: #f8fafc; font-family: {FONT_STACK};">
  <defs>
    <filter id="shadowUp" x="-5%" y="-3%" width="110%" height="110%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0f172a" flood-opacity="0.06" />
      <feDropShadow dx="0" dy="1" stdDeviation="2" flood-color="#0f172a" flood-opacity="0.04" />
    </filter>

    <linearGradient id="headerGradUp" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#047857" />
      <stop offset="100%" stop-color="#10b981" />
    </linearGradient>

    <linearGradient id="cardGradUp" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" />
      <stop offset="100%" stop-color="#f8fafc" />
    </linearGradient>

    <marker id="arrowUp" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#10b981" />
    </marker>
  </defs>

  <!-- Canvas Background -->
  <rect width="920" height="1320" fill="#f8fafc" />

  <!-- Outer Border Container -->
  <rect x="20" y="20" width="880" height="1280" rx="20" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.5" filter="url(#shadowUp)" />

  <!-- Header Banner -->
  <g transform="translate(20, 20)">
    <path d="M 0 20 Q 0 0 20 0 L 860 0 Q 880 0 880 20 L 880 90 L 0 90 Z" fill="url(#headerGradUp)" />
    
    <!-- Top Badge -->
    <rect x="28" y="16" width="180" height="22" rx="11" fill="#ffffff" fill-opacity="0.2" />
    <text x="118" y="31" text-anchor="middle" fill="#ffffff" font-size="11" font-weight="700" letter-spacing="0.8">PART 2: REVIEW &amp; EDITING</text>

    <text x="28" y="62" fill="#ffffff" font-size="22" font-weight="800">Multi-Wiki Publishing Workflow</text>
    <text x="28" y="80" fill="#d1fae5" font-size="12">update_wiki.py • Sixel in-terminal preview, colored diffs, and multi-wiki wikitext &amp; Wikidata P18 editing</text>
  </g>

  <!-- STEP 1: Resumable Session Manager -->
  <g transform="translate(50, 135)">
    <rect width="820" height="135" rx="14" fill="url(#cardGradUp)" stroke="#cbd5e1" stroke-width="1.2" filter="url(#shadowUp)" />
    
    <rect x="20" y="16" width="65" height="22" rx="11" fill="#ecfdf5" />
    <text x="52" y="31" text-anchor="middle" fill="#059669" font-size="11" font-weight="800">STEP 01</text>
    <text x="96" y="32" fill="#0f172a" font-size="16" font-weight="700">Load Tasks &amp; Atomic Progress Tracking</text>
    <text x="20" y="60" fill="#475569" font-size="13">Loads candidates from results.json and syncs with results.progress.json:</text>

    <!-- Resumable Callout Grid -->
    <g transform="translate(20, 75)">
      <rect width="380" height="44" rx="8" fill="#f8fafc" stroke="#cbd5e1" />
      <text x="16" y="20" fill="#0f172a" font-size="12" font-weight="700">Atomic State: results.progress.json</text>
      <text x="16" y="36" fill="#64748b" font-size="11">Tracks updated, skipped, and remaining tasks</text>

      <rect x="400" y="0" width="380" height="44" rx="8" fill="#ecfdf5" stroke="#a7f3d0" />
      <text x="416" y="20" fill="#065f46" font-size="12" font-weight="700">Safe Breaks Anytime: Press [q] or Ctrl+C</text>
      <text x="416" y="36" fill="#047857" font-size="11">Resume later exactly where you stopped!</text>
    </g>
  </g>

  <!-- Connector 1 -> 2 -->
  <path d="M 460 270 L 460 295" stroke="#10b981" stroke-width="2.5" marker-end="url(#arrowUp)" fill="none" />

  <!-- STEP 2: Sixel Preview -->
  <g transform="translate(50, 300)">
    <rect width="820" height="120" rx="14" fill="url(#cardGradUp)" stroke="#cbd5e1" stroke-width="1.2" filter="url(#shadowUp)" />
    
    <rect x="20" y="16" width="65" height="22" rx="11" fill="#ecfdf5" />
    <text x="52" y="31" text-anchor="middle" fill="#059669" font-size="11" font-weight="800">STEP 02</text>
    <text x="96" y="32" fill="#0f172a" font-size="16" font-weight="700">In-Terminal Sixel Photo Preview</text>
    <text x="20" y="60" fill="#475569" font-size="13">Downloads thumbnail and renders in true-color directly inside your terminal:</text>

    <!-- Preview Pills -->
    <g transform="translate(20, 75)">
      <rect width="250" height="30" rx="6" fill="#f8fafc" stroke="#e2e8f0" />
      <circle cx="16" cy="15" r="4" fill="#10b981" />
      <text x="28" y="20" fill="#334155" font-size="12" font-weight="600">Graphics engine: chafa -f sixel</text>

      <rect x="265" y="0" width="270" height="30" rx="6" fill="#f8fafc" stroke="#e2e8f0" />
      <circle cx="281" cy="15" r="4" fill="#10b981" />
      <text x="293" y="20" fill="#334155" font-size="12" font-weight="600">Instant visual portrait verification</text>

      <rect x="550" y="0" width="230" height="30" rx="6" fill="#f8fafc" stroke="#e2e8f0" />
      <circle cx="566" cy="15" r="4" fill="#10b981" />
      <text x="578" y="20" fill="#334155" font-size="12" font-weight="600">Fallbacks: symbols or none</text>
    </g>
  </g>

  <!-- Connector 2 -> 3 -->
  <path d="M 460 420 L 460 445" stroke="#10b981" stroke-width="2.5" marker-end="url(#arrowUp)" fill="none" />

  <!-- STEP 3: Wikitext Diff Preview -->
  <g transform="translate(50, 450)">
    <rect width="820" height="145" rx="14" fill="url(#cardGradUp)" stroke="#cbd5e1" stroke-width="1.2" filter="url(#shadowUp)" />
    
    <rect x="20" y="16" width="65" height="22" rx="11" fill="#ecfdf5" />
    <text x="52" y="31" text-anchor="middle" fill="#059669" font-size="11" font-weight="800">STEP 03</text>
    <text x="96" y="32" fill="#0f172a" font-size="16" font-weight="700">Unified Color Wikitext Diff Preview</text>
    <text x="20" y="58" fill="#475569" font-size="13">Inspect exact modifications before confirming any edit:</text>

    <!-- Terminal Diff Mockup -->
    <g transform="translate(20, 72)">
      <rect width="780" height="58" rx="8" fill="#0f172a" />
      <circle cx="16" cy="16" r="4" fill="#ef4444" />
      <circle cx="28" cy="16" r="4" fill="#f59e0b" />
      <circle cx="40" cy="16" r="4" fill="#10b981" />
      <text x="16" y="36" fill="#ef4444" font-family="'Nirmala UI', 'DejaVu Sans Mono', monospace" font-size="12">- | படம் = </text>
      <text x="16" y="50" fill="#22c55e" font-family="'Nirmala UI', 'DejaVu Sans Mono', monospace" font-size="12">+ | படம் = Ramchundra.jpg</text>
      <text x="420" y="44" fill="#94a3b8" font-family="'Nirmala UI', 'DejaVu Sans', sans-serif" font-size="11">(or localized lead image prefix [[படிமம்:...]])</text>
    </g>
  </g>

  <!-- Connector 3 -> 4 -->
  <path d="M 460 595 L 460 620" stroke="#10b981" stroke-width="2.5" marker-end="url(#arrowUp)" fill="none" />

  <!-- STEP 4: Interactive Decision Prompt -->
  <g transform="translate(50, 625)">
    <rect width="820" height="220" rx="14" fill="url(#cardGradUp)" stroke="#cbd5e1" stroke-width="1.2" filter="url(#shadowUp)" />
    
    <rect x="20" y="16" width="65" height="22" rx="11" fill="#ecfdf5" />
    <text x="52" y="31" text-anchor="middle" fill="#059669" font-size="11" font-weight="800">STEP 04</text>
    <text x="96" y="32" fill="#0f172a" font-size="16" font-weight="700">Interactive Editor Decision Prompt</text>
    <text x="20" y="60" fill="#475569" font-size="13">Choose your action at the terminal prompt for each article:</text>

    <!-- Options Grid -->
    <g transform="translate(20, 75)">
      <!-- Option A -->
      <rect width="380" height="42" rx="8" fill="#ecfdf5" stroke="#10b981" stroke-width="1.5" />
      <rect x="8" y="8" width="85" height="26" rx="4" fill="#10b981" />
      <text x="50" y="25" text-anchor="middle" fill="#ffffff" font-size="12" font-weight="800">[a]ll</text>
      <text x="102" y="26" fill="#065f46" font-size="12" font-weight="700">Update ALL Missing Wikis + Wikidata P18</text>

      <!-- Option Y -->
      <g transform="translate(400, 0)">
        <rect width="380" height="42" rx="8" fill="#eff6ff" stroke="#bfdbfe" />
        <rect x="8" y="8" width="85" height="26" rx="4" fill="#3b82f6" />
        <text x="50" y="25" text-anchor="middle" fill="#ffffff" font-size="12" font-weight="800">[y]es</text>
        <text x="102" y="26" fill="#1e40af" font-size="12" font-weight="700">Publish to Primary Wiki Only (e.g. Tamil)</text>
      </g>

      <!-- Option W -->
      <g transform="translate(0, 48)">
        <rect width="380" height="42" rx="8" fill="#faf5ff" stroke="#e9d5ff" />
        <rect x="8" y="8" width="85" height="26" rx="4" fill="#8b5cf6" />
        <text x="50" y="25" text-anchor="middle" fill="#ffffff" font-size="12" font-weight="800">[w]ikidata</text>
        <text x="102" y="26" fill="#6b21a8" font-size="12" font-weight="700">Add Property P18 to Wikidata Only</text>
      </g>

      <!-- Option C -->
      <g transform="translate(400, 48)">
        <rect width="380" height="42" rx="8" fill="#f8fafc" stroke="#cbd5e1" />
        <rect x="8" y="8" width="85" height="26" rx="4" fill="#64748b" />
        <text x="50" y="25" text-anchor="middle" fill="#ffffff" font-size="12" font-weight="800">[c]hoose</text>
        <text x="102" y="26" fill="#334155" font-size="12" font-weight="700">Select Specific Wikis (e.g. enter: ta, ml)</text>
      </g>

      <!-- Option N -->
      <g transform="translate(0, 96)">
        <rect width="380" height="38" rx="8" fill="#fff1f2" stroke="#fecdd3" />
        <rect x="8" y="6" width="85" height="26" rx="4" fill="#f43f5e" />
        <text x="50" y="23" text-anchor="middle" fill="#ffffff" font-size="12" font-weight="800">[n]o</text>
        <text x="102" y="24" fill="#9f1239" font-size="12" font-weight="700">Skip to Next Article (marked as skipped)</text>
      </g>

      <!-- Option Q -->
      <g transform="translate(400, 96)">
        <rect width="380" height="38" rx="8" fill="#f1f5f9" stroke="#cbd5e1" />
        <rect x="8" y="6" width="85" height="26" rx="4" fill="#475569" />
        <text x="50" y="23" text-anchor="middle" fill="#ffffff" font-size="12" font-weight="800">[q]uit</text>
        <text x="102" y="24" fill="#334155" font-size="12" font-weight="700">Save Progress &amp; Pause Session Safely</text>
      </g>
    </g>
  </g>

  <!-- Connector 4 -> 5 -->
  <path d="M 460 845 L 460 870" stroke="#10b981" stroke-width="2.5" marker-end="url(#arrowUp)" fill="none" />

  <!-- STEP 5: Publishing Engine -->
  <g transform="translate(50, 875)">
    <rect width="820" height="155" rx="14" fill="url(#cardGradUp)" stroke="#cbd5e1" stroke-width="1.2" filter="url(#shadowUp)" />
    
    <rect x="20" y="16" width="65" height="22" rx="11" fill="#ecfdf5" />
    <text x="52" y="31" text-anchor="middle" fill="#059669" font-size="11" font-weight="800">STEP 05</text>
    <text x="96" y="32" fill="#0f172a" font-size="16" font-weight="700">Multi-Wiki Publishing Engine with Native Syntax</text>
    <text x="20" y="60" fill="#475569" font-size="13">Logs in using a Wikimedia Bot Password and edits each language wiki with its native prefixes:</text>

    <!-- Syntax Cards Grid -->
    <g transform="translate(20, 75)">
      <rect width="250" height="65" rx="8" fill="#f8fafc" stroke="#e2e8f0" />
      <text x="16" y="24" fill="#0f172a" font-size="12" font-weight="700">ta: Tamil Wikipedia</text>
      <text x="16" y="42" fill="#2563eb" font-family="'Nirmala UI', 'Noto Sans Tamil', monospace" font-size="11">[[படிமம்:...]]</text>
      <text x="16" y="56" fill="#64748b" font-family="'Nirmala UI', 'Noto Sans Tamil', monospace" font-size="11">| படம் = ...</text>

      <rect x="265" y="0" width="250" height="65" rx="8" fill="#f8fafc" stroke="#e2e8f0" />
      <text x="281" y="24" fill="#0f172a" font-size="12" font-weight="700">ml: Malayalam Wikipedia</text>
      <text x="281" y="42" fill="#059669" font-family="'Nirmala UI', 'Noto Sans Malayalam', monospace" font-size="11">[[പ്രമാണം:...]]</text>
      <text x="281" y="56" fill="#64748b" font-family="'Nirmala UI', 'Noto Sans Malayalam', monospace" font-size="11">| ചിത്രം = ...</text>

      <rect x="530" y="0" width="250" height="65" rx="8" fill="#f8fafc" stroke="#e2e8f0" />
      <text x="546" y="24" fill="#0f172a" font-size="12" font-weight="700">te: Telugu Wikipedia</text>
      <text x="546" y="42" fill="#7c3aed" font-family="'Nirmala UI', 'Noto Sans Telugu', monospace" font-size="11">[[దస్త్రం:...]]</text>
      <text x="546" y="56" fill="#64748b" font-family="'Nirmala UI', 'Noto Sans Telugu', monospace" font-size="11">| చిత్రం = ...</text>
    </g>
  </g>

  <!-- Connector 5 -> 6 -->
  <path d="M 460 1030 L 460 1055" stroke="#10b981" stroke-width="2.5" marker-end="url(#arrowUp)" fill="none" />

  <!-- STEP 6: Final Outcome -->
  <g transform="translate(50, 1060)">
    <rect width="820" height="180" rx="14" fill="#ecfdf5" stroke="#10b981" stroke-width="2" />
    
    <text x="20" y="32" fill="#065f46" font-size="15" font-weight="800">STAGE 2 DELIVERABLES: MULTI-WIKI ENRICHMENT</text>
    <text x="20" y="54" fill="#047857" font-size="13">Articles enriched with photos across language wikis &amp; Wikidata knowledge graph:</text>

    <!-- Outcome Cards -->
    <g transform="translate(20, 72)">
      <rect width="250" height="85" rx="8" fill="#ffffff" stroke="#a7f3d0" />
      <circle cx="20" cy="22" r="8" fill="#10b981" />
      <path d="M 16 22 L 19 25 L 25 19" stroke="#ffffff" stroke-width="2" fill="none" />
      <text x="36" y="26" fill="#065f46" font-size="13" font-weight="700">Tamil Wikipedia Updated</text>
      <text x="16" y="52" fill="#475569" font-size="11">Infobox or lead image embedded</text>
      <text x="16" y="68" fill="#059669" font-size="11" font-weight="600">Local readers see photo!</text>

      <rect x="265" y="0" width="250" height="85" rx="8" fill="#ffffff" stroke="#a7f3d0" />
      <circle cx="285" cy="22" r="8" fill="#10b981" />
      <path d="M 281 22 L 284 25 L 290 19" stroke="#ffffff" stroke-width="2" fill="none" />
      <text x="301" y="26" fill="#065f46" font-size="13" font-weight="700">Sibling Wikis Updated</text>
      <text x="281" y="52" fill="#475569" font-size="11">Malayalam, Telugu, Hindi, etc.</text>
      <text x="281" y="68" fill="#059669" font-size="11" font-weight="600">Single-click mass enrichment!</text>

      <rect x="530" y="0" width="250" height="85" rx="8" fill="#ffffff" stroke="#a7f3d0" />
      <circle cx="550" cy="22" r="8" fill="#10b981" />
      <path d="M 546 22 L 549 25 L 555 19" stroke="#ffffff" stroke-width="2" fill="none" />
      <text x="566" y="26" fill="#065f46" font-size="13" font-weight="700">Wikidata Item Enriched</text>
      <text x="546" y="52" fill="#475569" font-size="11">Property P18 added to entity</text>
      <text x="546" y="68" fill="#059669" font-size="11" font-weight="600">Enriches 50+ language wikis!</text>
    </g>
  </g>
</svg>"""


def main():
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
    os.makedirs(docs_dir, exist_ok=True)

    # 1. Generate find_photos_flow.svg and .png
    find_svg_path = os.path.join(docs_dir, "find_photos_flow.svg")
    find_png_path = os.path.join(docs_dir, "find_photos_flow.png")
    with open(find_svg_path, "w", encoding="utf-8") as f:
        f.write(FIND_SVG)
    print(f"[✓] Saved SVG: {find_svg_path}")

    png_data_find = cairosvg.svg2png(bytestring=FIND_SVG.encode("utf-8"), dpi=200)
    with open(find_png_path, "wb") as f:
        f.write(png_data_find)
    print(f"[✓] Rendered PNG: {find_png_path} ({len(png_data_find)} bytes)")

    # 2. Generate update_wiki_flow.svg and .png
    update_svg_path = os.path.join(docs_dir, "update_wiki_flow.svg")
    update_png_path = os.path.join(docs_dir, "update_wiki_flow.png")
    with open(update_svg_path, "w", encoding="utf-8") as f:
        f.write(UPDATE_SVG)
    print(f"[✓] Saved SVG: {update_svg_path}")

    png_data_update = cairosvg.svg2png(bytestring=UPDATE_SVG.encode("utf-8"), dpi=200)
    with open(update_png_path, "wb") as f:
        f.write(png_data_update)
    print(f"[✓] Rendered PNG: {update_png_path} ({len(png_data_update)} bytes)")


if __name__ == "__main__":
    main()
