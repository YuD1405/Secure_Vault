function showToast(message, type = 'error') {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerText = message;

  container.appendChild(toast);

  // Hiện animation
  setTimeout(() => {
    toast.classList.add("show");
  }, 10);

  // Tự ẩn sau 3s
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => container.removeChild(toast), 300);
  }, 3000);
}
