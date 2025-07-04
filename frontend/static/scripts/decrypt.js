document.addEventListener("DOMContentLoaded", () => {
  // 🔒 Ngăn kéo file toàn trang
  window.addEventListener("dragover", e => e.preventDefault());
  window.addEventListener("drop", e => e.preventDefault());

  // 🧭 Sidebar hover mở rộng
  const sidebar = document.querySelector(".sidebar");
  const mainToggle = document.querySelector(".main");
  if (sidebar && mainToggle) {
    sidebar.addEventListener("mouseover", () => mainToggle.classList.add("active"));
    sidebar.addEventListener("mouseout", () => mainToggle.classList.remove("active"));
  }

  // 📦 Gán DOM cho encrypt form
  const dropArea = document.getElementById("drop-area");
  const fileInput = document.getElementById("file-upload");
  const fileDisplay = document.getElementById("file-upload-show");
  const fileIcon = document.getElementById("file-icon");
  const fileDetails = document.getElementById("file-details");
  const form = document.getElementById("uploadForm");
  const resultDisplay = document.getElementById("uploadResult");

  if (!dropArea || !fileInput || !fileDisplay || !form || !fileIcon || !fileDetails) return;

  // 🖱️ Khi chọn file thủ công
  fileInput.addEventListener("change", function () {
    const file = this.files[0];
    updatePreview(file, fileDisplay, fileIcon, fileDetails);
    updateDecryptionModeDisplay();
  });

  // 🚀 Submit form Encrypt
  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const file = fileInput.files[0];
    if (!file) {
      showToast("Vui lòng chọn file để giải mã!", "error");
      return;
    }

    const formData = new FormData();
    formData.append("file_to_decrypt", file);

    try {
      const res = await fetch("/crypto/decrypt", {
        method: "POST",
        body: formData
      });

      const contentType = res.headers.get("Content-Type");

      if (!res.ok) {
        // Nếu server trả về lỗi dưới dạng JSON
        if (contentType && contentType.includes("application/json")) {
          const errorData = await res.json();
          showToast(errorData.message || "Giải mã thất bại", "error");
        } else {
          const errorText = await res.text();
          showToast("Lỗi không xác định: " + errorText, "error");
        }
        return;
      }

      // Nếu thành công → file trả về → tải xuống
      const blob = await res.blob();
      const disposition = res.headers.get("Content-Disposition");
      let filename = "decrypted_file.dat";

      // Tìm tên file từ header
      if (disposition && disposition.includes("filename=")) {
        const match = disposition.match(/filename="?(.+)"?/);
        if (match && match[1]) {
          filename = match[1];
        }
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      showToast("Giải mã và tải xuống thành công!", "success");

    } catch (err) {
      console.error(err);
      showToast("Lỗi khi gửi yêu cầu giải mã", "error");
    }
  });


  // ☁️ Drag & Drop
  setupDropEvents(dropArea, fileInput, fileDisplay, fileIcon, fileDetails);
});

// ✅ Preview file
function updatePreview(file, displayEl, iconEl, detailEl) {
  if (!file) return;
  displayEl.value = file.name;
  iconEl.src = getFileIcon(file.name);
  iconEl.style.display = "inline";
  detailEl.innerText = `${file.type || "Unknown type"} • ${formatFileSize(file.size)}`;
}

// ✅ Drag & Drop setup
function setupDropEvents(area, inputEl, displayEl, iconEl, detailEl) {
  ["dragenter", "dragover", "dragleave", "drop"].forEach(event =>
    area.addEventListener(event, e => {
      e.preventDefault();
      e.stopPropagation();
    })
  );

  ["dragenter", "dragover"].forEach(event =>
    area.addEventListener(event, () => area.classList.add("highlight"))
  );

  ["dragleave", "drop"].forEach(event =>
    area.addEventListener(event, () => area.classList.remove("highlight"))
  );

  area.addEventListener("drop", e => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      inputEl.files = files;
      updatePreview(files[0], displayEl, iconEl, detailEl);
    }
  });
}

// 🧠 Icon theo loại file
function getFileIcon(fileName) {
  const ext = fileName.split('.').pop().toLowerCase();
  switch (ext) {
    case 'pdf': return '/static/icons/pdf.png';
    case 'docx': return '/static/icons/doc.png';
    case 'txt': return '/static/icons/txt.png';
    default: return '/static/icons/file.png';
  }
}

// 📐 Định dạng dung lượng
function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

function updateDecryptionModeDisplay() {
  const encFile = document.getElementById("file-upload").files[0];
  const modeDisplay = document.getElementById("decryption-mode-display");

  modeDisplay.classList.remove("split", "combined", "unknown");

  if (!encFile) {
    modeDisplay.innerText = "Unknown";
    modeDisplay.classList.add("unknown");
    return;
  }

  const fileName = encFile.name.toLowerCase();

  if (fileName.endsWith(".zip")) {
    modeDisplay.innerText = "Split (.enc + .key in zip)";
    modeDisplay.classList.add("split");
  } else if (fileName.endsWith(".enc")) {
    modeDisplay.innerText = "Combined (.enc only)";
    modeDisplay.classList.add("combined");
  } else {
    modeDisplay.innerText = "Unknown format";
    modeDisplay.classList.add("unknown");
  }
}
