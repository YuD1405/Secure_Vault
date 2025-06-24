document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.querySelector(".sidebar");
  const mainToggle = document.querySelector(".main");
  const tabToggle = document.querySelector(".tab-pane");

  sidebar.addEventListener("mouseover", () => {
    mainToggle.classList.add("active");
  });

  sidebar.addEventListener("mouseout", () => {
    mainToggle.classList.remove("active");
  });
});

function switchTab(tabElement, tabId) {
    document.querySelectorAll(".tab-item").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

    tabElement.classList.add("active");
    document.getElementById(tabId).classList.add("active");
}

function copyToClipboard() {
    const input = document.getElementById("manual-code-input");
    input.select();
    input.setSelectionRange(0, 99999);
    navigator.clipboard.writeText(input.value);
    showToast("Copied to clipboard!");
}

function downloadQR() {
    const qrImg = document.getElementById("qr-img");
    const link = document.createElement("a");
    link.href = qrImg.src;
    link.download = "my_qr_code.png";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
