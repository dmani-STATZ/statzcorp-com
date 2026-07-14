# How to Add and Use Videos

Quick reference for uploading marketing videos, sharing them in email, and embedding them on site pages. Admin UI labels match Django admin as of this guide.

---

## Part 1 — Content Managers (no coding)

### Log in

1. On any public page, scroll to the footer and click **Log In**.
2. Sign in with your Django admin username and password.
3. You land in the STATZ admin home.

### Upload a new video

1. In the admin sidebar, open **Videos** → **Video assets** → **Add video asset**.
2. Fill in:
   - **Title** — display name. The **Slug** (short URL name, e.g. `team-statz`) fills in automatically from the title; leave it unless you need a custom path.
   - **Description** — optional; shown on the public landing page.
   - **Video file** — choose the file. Allowed extensions: **mp4, webm, ogg, mov, m4v**.
   - **Thumbnail** — optional image. Used as the video player poster and in email/link previews. Email clients cannot play video; the thumbnail is what recipients see.
3. Leave **Is published** unchecked until you are ready for the public to see it.
4. Click **Save**.

### Publish (or stage)

- Unchecked **Is published**: the video is not on the public site. Visiting its landing page returns “not found.” Use this to finish uploading and checking links before release.
- Checked **Is published**: the landing page and any embeds that use that video become available.

### After saving — Share Links

Open the saved video asset. The **Share Links** section appears after the first save:

| Field | What it is | When to use it |
|-------|------------|----------------|
| **Public video URL** | Direct link to the video file itself. Use **Copy** or select the text box. | Rare — raw file linking only. |
| **Landing page URL** | Branded site page (path like `/videos/your-slug/`). Click **Open landing page** to preview. | **Use this in emails.** Prepend your site domain (e.g. `https://yoursite.example` + the path). |

### Use a video in an email

1. Copy the **landing page** URL (full site URL + path from Share Links).
2. Paste that link in the email (button or text).
3. Optional: insert the thumbnail image into the email body and hyperlink it to the same landing page URL.

Videos cannot play inside emails. That is an email-client limitation, not a site bug.

### Practical notes

- Large files take time. Do not close the browser tab mid-upload. Django admin has no upload progress bar.
- Prefer **MP4 (H.264)** at a web-friendly bitrate for the widest browser support.
- Django allows requests up to about **1 GB**; very large files may still fail on the server side (see Troubleshooting).

### Replace or delete

- **Replace:** Open the Video asset, choose a new file under **Video file** (and thumbnail if needed), then Save. The slug/landing path stays the same unless you change the slug.
- **Delete:** Use delete on that Video asset. Any previously shared landing-page or file links to it will break.

---

## Part 2 — Developers (embed on pages)

Never put video files under `{% static %}`. Manifest static storage will 500 the page if the file is missing. All videos go through `VideoAsset`.

```django
{% load video_tags %}
{% get_video 'the-video-slug' as my_video %}
{% if my_video %}
  {% include 'videos/_video_embed.html' with video=my_video inline_player=True %}
{% endif %}
```

- `get_video` returns only **published** assets (or nothing).
- `inline_player=True` — embedded HTML5 player on the page.
- Omit `inline_player` (or leave it false) — clickable thumbnail card that links to the landing page.

**Where files live:** Azure Blob Storage (`media` container) when `AZURE_CONNECTION_STRING` is set; otherwise the local `media/` folder. Always use `video.video_file.url` / `video.thumbnail.url` in templates.

---

## Part 3 — Troubleshooting

| Problem | What to check |
|---------|----------------|
| Video page says not found | **Is published** must be checked. |
| Video won’t play in the browser | Prefer MP4/H.264. Some MOV codecs upload fine but won’t play in browsers. |
| Upload fails immediately | File may exceed the ~1 GB upload cap, or the extension is not in mp4/webm/ogg/mov/m4v. |
| Upload hangs, then errors on a very large file | Likely a server timeout. Contact the site administrator — Gunicorn timeout is a deployment setting (see `CONTEXT.md`). |

**Who to contact:** See **Stakeholders / Points of Contact** in `CONTEXT.md` (primary technical / IT & Manufacturing Operations contact for this site).
