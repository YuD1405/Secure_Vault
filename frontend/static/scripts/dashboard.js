function redirectToDashboard() {
  const url = document.querySelector(".logo").dataset.href;
  window.location.href = url;
}

// Đánh dấu mục đang active
document.addEventListener("DOMContentLoaded", () => {
  const links = document.querySelectorAll(".sidebar-menu a");
  const currentUrl = window.location.href;

  links.forEach((link) => {
    if (currentUrl.includes(link.href)) {
      link.classList.add("active");
    }
  });
});
