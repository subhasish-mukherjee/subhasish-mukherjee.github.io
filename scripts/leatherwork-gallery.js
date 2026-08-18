(() => {
  const buildPhoto = (photo) => {
    const figure = document.createElement("figure");
    const link = document.createElement("a");
    const image = document.createElement("img");

    link.href = photo.src;
    link.target = "_blank";
    link.rel = "noopener";
    link.setAttribute("aria-label", `Open full-size image: ${photo.alt}`);

    image.src = photo.src;
    image.alt = photo.alt;
    image.loading = "lazy";
    link.append(image);
    figure.append(link);

    if (photo.caption) {
      const caption = document.createElement("figcaption");
      caption.textContent = photo.caption;
      figure.append(caption);
    }

    return figure;
  };

  const loadGallery = async (container) => {
    const url = container.dataset.galleryUrl;
    const mode = container.dataset.galleryMode || "all";
    const emptyMessage = container.dataset.emptyMessage || "No photos yet.";

    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Could not load ${url}`);

      const manifest = await response.json();
      const photos = Array.isArray(manifest.photos) ? manifest.photos : [];
      const selected = mode === "featured"
        ? photos.filter((photo) => photo.featured).slice(0, 3)
        : photos;

      if (selected.length === 0) {
        const empty = document.createElement("p");
        empty.className = "gallery-empty";
        empty.textContent = emptyMessage;
        container.append(empty);
        return;
      }

      selected.forEach((photo) => container.append(buildPhoto(photo)));
    } catch (error) {
      console.error("Unable to load leatherwork gallery", error);
    }
  };

  document.querySelectorAll(".leatherwork-gallery[data-gallery-url]").forEach(loadGallery);
})();
