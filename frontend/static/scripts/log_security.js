document.addEventListener("DOMContentLoaded", () => {
  async function fetchAndRenderLogs() {
    try {
      const res = await fetch("/utils/log_security", {
        headers: { "X-Requested-With": "XMLHttpRequest" }
      });
      const html = await res.text();

      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");
      const newTable = doc.querySelector("#logTable");

      if (newTable) {
        document.getElementById("logTable").replaceWith(newTable);
        showToast("✅ Refreshed security logs", "success");
      } else {
        showToast("⚠️ Failed to refresh table (empty content)", "warning");
      }
    } catch (err) {
      showToast("❌ Error refreshing logs", "error");
      console.error("Refresh error:", err);
    }
  }

  // Tự động gọi khi vừa load trang
  fetchAndRenderLogs();

  const refreshBtn = document.getElementById("refreshBtn");

  if (refreshBtn) {
    refreshBtn.addEventListener("click", fetchAndRenderLogs);
  }
});

