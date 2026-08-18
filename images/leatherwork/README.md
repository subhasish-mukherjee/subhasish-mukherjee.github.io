# Leatherwork photos

Put all leatherwork images in [`photos/`](photos/), then list them in
[`gallery.json`](gallery.json). The gallery automatically uses that file in two
places: the three featured images on the Other Interests & Projects page and
the full [Leatherwork Gallery](../../leatherwork.qmd).

Use the following shape for every photo in `gallery.json`:

```json
{
  "src": "images/leatherwork/photos/01-bifold-wallet.jpg",
  "alt": "Hand-stitched brown bifold wallet open on a workbench",
  "caption": "Bifold wallet in natural vegetable-tanned leather.",
  "featured": true
}
```

- `src` is required and must match the image's filename exactly.
- `alt` is required; briefly describe what is visible in the photo.
- `caption` is optional. Omit it when the image does not need one.
- Set `featured` to `true` on exactly three photos. Those appear first on the
  Other Interests & Projects page; every photo appears in the full gallery.

Keep the entries inside the `"photos"` array, separated by commas. Add roughly
20–30 entries as photos become available. Use web-friendly `.jpg` or `.webp`
files, with a longest side around 1600–2400 pixels so the gallery stays fast.

Before publishing phone photos, remove embedded location metadata. If you add
more photos and ask Codex to publish them, it will check and sanitize them for
you.
