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
      showToast("Please select a file first!", "error");
      return;
    }

    const formData = new FormData();
    formData.append("file_to_sign", file);

    try {
      const res = await fetch("/utils/sign_file", {
        method: "POST",
        body: formData
      });
      console.log(res);
      const contentType = res.headers.get("Content-Type");

      if (res.ok && contentType === "application/octet-stream") {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = file.name + ".sig";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        URL.revokeObjectURL(url);

        showToast("Digital signature successful! Your file is being downloaded.", "success");
      } else {
        // ❌ Trường hợp lỗi - trả về JSON
        const result = await res.json();
        const message = result.message || result.error || "Error occured.";
        showToast(message, "error");
      }
    } catch (err) {
      console.error(err);
      showToast("Failed to upload file", "error");
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

// 🧠 Icon theo loại file
function getFileIcon(fileName) {
  const ext = fileName.split('.').pop().toLowerCase();
  switch (ext) {
    case 'pdf':
      return '/static/icons/pdf.png';
    case 'docx':
    case 'doc':
      return '/static/icons/doc.png';
    case 'txt':
      return '/static/icons/txt.png';
    case 'key':
      return '/static/icons/key.png';         // 🔑 file key AES
    case 'enc':
      return '/static/icons/locked.png';        // 🔒 file mã hóa
    case 'zip':
      return '/static/icons/zip.png';
    case 'mp4':
    case 'avi':
    case 'mov':
    case 'mkv':
      return '/static/icons/video.png';       // 🎞️ video file
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'gif':
    case 'webp':
    case 'bmp':
      return '/static/icons/gallery.png'; 
    default:
      return '/static/icons/file.png';        // 📄 mặc định
  }
}
