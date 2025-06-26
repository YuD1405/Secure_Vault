document.addEventListener("DOMContentLoaded", () => {
  // 🔒 1. Chặn mặc định hành vi kéo file vào toàn trang (mở PDF)
  window.addEventListener("dragover", e => e.preventDefault());
  window.addEventListener("drop", e => e.preventDefault());

  // 🧭 2. Sidebar hover mở rộng main
  const sidebar = document.querySelector(".sidebar");
  const mainToggle = document.querySelector(".main");
  if (sidebar && mainToggle) {
    sidebar.addEventListener("mouseover", () => mainToggle.classList.add("active"));
    sidebar.addEventListener("mouseout", () => mainToggle.classList.remove("active"));
  }

  // 📦 3. Gán DOM
  const dropArea = document.getElementById("drop-area");
  const fileInput = document.getElementById("file-upload");
  const fileDisplay = document.getElementById("file-upload-show");
  const form = document.getElementById("uploadForm");
  const resultDisplay = document.getElementById("uploadResult");

  if (!dropArea || !fileInput || !fileDisplay || !form || !resultDisplay) return;

  // 🖱️ 4. Chọn file thủ công → hiển thị tên
  fileInput.addEventListener("change", function () {
    const file = this.files[0];
    if (file) {
        fileDisplay.value = file.name;
        const iconPath = getFileIcon(file.name);
        document.getElementById("file-icon").src = iconPath;
        document.getElementById("file-icon").style.display = "inline";
        document.getElementById("file-details").innerText = `${file.type || "Unknown type"} • ${formatFileSize(file.size)}`;
    }
  });

  // 📤 5. Gửi form qua fetch
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const file = fileInput.files[0];

    if (!file) {
      // resultDisplay.innerText = "Please select a file first!";
      // resultDisplay.classList.remove("success");
      // resultDisplay.classList.add("error");
      showToast("Please select a file first!", "error");
      return;
    }

    const formData = new FormData();
    formData.append("file_to_decrypt", file);

    try {
      const res = await fetch("/crypto/decrypt", {
        method: "POST",
        body: formData
      });
      const result = await res.json();
      resultDisplay.classList.remove("error", "success");

      if (result.error) {
        // resultDisplay.innerText = result.error;
        // resultDisplay.classList.add("error");
        showToast(result.error, "error");
      } else if (result.message) {
        // resultDisplay.innerText = result.message;
        // resultDisplay.classList.add("success");
        showToast(result.message, "success");
      } else {
        // resultDisplay.innerText = "Đã gửi!";
        showToast("Đã gửi!", "success");
      }
    } catch (err) {
      // resultDisplay.innerText = "Lỗi khi gửi file.";
      console.error(err);
      showToast("Lỗi khi gửi file", "error");
    }
  });

  // 🎯 6. Drag & drop vào drop-area
  ["dragenter", "dragover", "dragleave", "drop"].forEach(eventName => {
    dropArea.addEventListener(eventName, e => {
      e.preventDefault();
      e.stopPropagation();
    });
  });

  ["dragenter", "dragover"].forEach(eventName => {
    dropArea.addEventListener(eventName, () => dropArea.classList.add("highlight"));
  });

  ["dragleave", "drop"].forEach(eventName => {
    dropArea.addEventListener(eventName, () => dropArea.classList.remove("highlight"));
  });

  dropArea.addEventListener("drop", e => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        fileInput.files = files;
        const file = files[0];
        fileDisplay.value = file.name;
        const iconPath = getFileIcon(file.name);
        document.getElementById("file-icon").src = iconPath;
        document.getElementById("file-icon").style.display = "inline";
        document.getElementById("file-details").innerText = `${file.type || "Unknown type"} • ${formatFileSize(file.size)}`;
    }
  });
});

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  else if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  else return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

function getFileIcon(fileName) {
  const ext = fileName.split('.').pop().toLowerCase();
  switch (ext) {
    case 'pdf':
      return '/static/icons/pdf.png';
    case 'doc':
    case 'docx':
      return '/static/icons/doc.png';
    case 'txt':
      return '/static/icons/txt.png';
    default:
      return '/static/icons/file.png';
  }
}
