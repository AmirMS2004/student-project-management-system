import client from "../api/client.js";

const PREVIEWABLE_EXTENSIONS = new Set([
  "pdf",
  "png",
  "jpg",
  "jpeg",
  "gif",
  "webp",
  "svg",
  "bmp",
]);

export function isPreviewable(filename) {
  const ext = filename?.split(".").pop()?.toLowerCase();
  return PREVIEWABLE_EXTENSIONS.has(ext);
}

/**
 * Fetches a protected file and either opens it inline (PDFs and images, via
 * the browser's native viewer) or triggers a normal download for everything
 * else.
 */
export async function openOrDownloadFile(url, filename) {
  const res = await client.get(url, { responseType: "blob" });
  const contentType = res.headers["content-type"];
  const blob = contentType ? new Blob([res.data], { type: contentType }) : res.data;
  const blobUrl = window.URL.createObjectURL(blob);

  if (isPreviewable(filename)) {
    window.open(blobUrl, "_blank", "noopener,noreferrer");
    // Revoke later so the newly opened tab has time to load the resource.
    setTimeout(() => window.URL.revokeObjectURL(blobUrl), 30000);
  } else {
    const link = document.createElement("a");
    link.href = blobUrl;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(blobUrl);
  }
}
