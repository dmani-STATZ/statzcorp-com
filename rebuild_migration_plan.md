# STATZ Corporation Website Migration & Redesign Plan (2026)

This document outlines the step-by-step roadmap for updating the STATZ Corporation web application from its previous red color scheme and layout to a modern, patriotic, and highly functional Django site.

---

## 🎨 1. Brand Identity & UI Redesign

### Color Palette Shift
* **Goal**: Replace the aggressive red (`#c9222a`) to eliminate "warning/error" visual indicators, replacing it with a sophisticated, patriotic theme.
* **Palette Proposal**:
  * **Primary (Deep Navy)**: `#1a2540` (represents stability, trust, and naval forces)
  * **Secondary (Patriotic Blue)**: `#003366` / `#002147`
  * **Accent (Military Gold/Brass)**: `#d4af37` / `#c5a059` (adds premium finish, represents insignia, stars, and defense honors)
  * **Backgrounds**: High-contrast white (`#ffffff`) and soft warm gray (`#f9f9fb`)

### Main Image / Slideshow Refactoring
* **Goal**: Represent all military branches (Army, Navy, Air Force, Marines, Coast Guard, Space Force) instead of just the single airplane (Air Force).
* **Implementation**:
  * Replace the hero image slider with a custom grid or responsive carousel highlighting joint-force operations.
  * Sourced branch images showcasing tactical gear, logistics support, and ground troop operations.

---

## 🧭 2. Navigation, Features & Integrations

### "Resources" Section
Add a new view and template `/resources/` featuring:
1. **CAGE Code Guide**: Steps to obtain and maintain a Commercial and Government Entity code.
2. **Joint Certification Program (JCP) Guide**: One-pager explaining DD Form 2345 submission for accessing export-controlled technical data.
3. **Shipping Preparation Checklist**: Guide covering labeling standards, pallet specifications, and avoiding packaging delays.

### News & Updates Engine
* Implement a simple `NewsPost` Django database model to support dated, chronological announcements.
* Sort queries by `-published_date` so new posts dynamically push older posts down.

### Microsoft Bookings Integration
* Replace plain forms with calendar booking embeds/links:
  * **Dion (IT & Manufacturing Operations)**
  * **Jenny/Chad (Accounting & Contract Administration)**
* Update site email addresses to point to direct, action-oriented inboxes instead of a centralized inbox.

---

## 📄 3. Content Refactoring

### Supply Chain Capabilities
* Rewrite contract administration and logistics copy.
* Explicitly mention capabilities in sourcing **NSNs (National Stock Numbers)**, **Federal Stock Classes (FSCs)**, machining tolerance checks, and raw materials.
* Remove obsolete references (e.g., **RYRAP**).

### Meet the Team
* Refactor to show a high-resolution team group photo.
* Drop individual name/bio cards to simplify maintenance and protect team privacy.

### Condensed About Us & History
* Condense the founding story and historical background.
* Remove references to General Patton.
* Update corporate metrics: *"STATZ Corp has helped 1,000+ suppliers win defense awards totaling over $17M+ as of 2026."*

### Certifications & Accreditations
* Introduce dynamic download links for three critical proof files:
  1. **ISO 9001 Certificate** (PDF)
  2. **SBA / SDVOSB Status Verification** (Screenshot proof)
  3. **CMMC Compliance Certificate** (PDF)

---

## 📈 4. Social & Video Marketing Roadmap

### LinkedIn Presence
* Establish a professional STATZ Corporation LinkedIn page.
* Focus content strictly on:
  * Supplier success stories.
  * Compliance updates (CMMC / NIST).
  * Award milestones.
* Restrict public comment fields to prevent spam or unmoderated political discourse.

### Video Content Production Setup
* **Hardware Checklist**:
  * **Camera**: Sony ZV-E10 or similar 4K vlog-capable mirrorless camera.
  * **Microphone**: Rode Wireless GO II or DJI Mic clip-on lapel.
  * **Lighting**: Godox SL60W with softbox diffuser for professional fill.
* **Hosting**: Serve videos via Azure CDN or high-speed self-hosted servers with appropriate bandwidth throttles.
