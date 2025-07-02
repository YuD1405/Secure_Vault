document.addEventListener("DOMContentLoaded", () => {
  // 🔒 1. Chặn hành vi mặc định khi kéo file vào toàn trang
  window.addEventListener("dragover", e => e.preventDefault());
  window.addEventListener("drop", e => e.preventDefault());

  // 🧭 2. Sidebar hover mở rộng main
  const sidebar = document.querySelector(".sidebar");
  const mainToggle = document.querySelector(".main");
  if (sidebar && mainToggle) {
    sidebar.addEventListener("mouseover", () => mainToggle.classList.add("active"));
    sidebar.addEventListener("mouseout", () => mainToggle.classList.remove("active"));
  }

  // 📦 3. Gán DOM cho 2 file input: encrypted + key
  const dropEnc = document.getElementById("drop-file");
  const dropKey = document.getElementById("drop-key");

  const encInput = document.getElementById("file-upload");
  const keyInput = document.getElementById("key-upload");

  const encDisplay = document.getElementById("file-upload-show");
  const encIcon = document.querySelectorAll("#file-icon")[0];
  const encDetails = document.getElementById("file-details-decrypt");

  const keyDisplay = document.getElementById("key-upload-show");
  const keyIcon = document.querySelectorAll("#file-icon")[1];
  const keyDetails = document.getElementById("file-details-key");

  const form = document.getElementById("uploadForm");
  const resultDisplay = document.getElementById("uploadResult");

  if (!dropEnc || !dropKey || !encInput || !keyInput || !form) return;

  // 🖱️ Khi chọn file bằng tay
  encInput.addEventListener("change", function () {
    updatePreview(this.files[0], encDisplay, encIcon, encDetails);
  });

  keyInput.addEventListener("change", function () {
    updatePreview(this.files[0], keyDisplay, keyIcon, keyDetails);
  });

  // 🚀 Submit giải mã
  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const encFile = encInput.files[0];
    const keyFile = keyInput.files[0];
    const mode = keyFile ? "splitted" : "combined";

    if (!encFile) {
      showToast("Vui lòng chọn file cần giải mã (.enc)!", "error");
      return;
    }

    const formData = new FormData();
    formData.append("file_to_decrypt", encFile);
    if (keyFile) formData.append("key_file", keyFile);
    formData.append("mode", mode);

    console.log("🚀 Sending decrypt:", {
      mode,
      enc: encFile.name,
      key: keyFile ? keyFile.name : "none"
    });

    try {
      const res = await fetch("/crypto/decrypt", {
        method: "POST",
        body: formData,
      });

      const result = await res.json();
      if (result.error) {
        showToast(result.error, "error");
      } else {
        showToast(result.message || "Giải mã thành công!", "success");
      }
    } catch (err) {
      console.error(err);
      showToast("Lỗi khi gửi yêu cầu giải mã", "error");
    }
  });

  // ☁️ Kích hoạt drag & drop
  setupDropEvents(dropEnc, encInput, encDisplay, encIcon, encDetails);
  setupDropEvents(dropKey, keyInput, keyDisplay, keyIcon, keyDetails);
});

// ✅ Hiển thị preview thông tin file
function updatePreview(file, displayEl, iconEl, detailEl) {
  if (!file) return;
  displayEl.value = file.name;
  iconEl.src = getFileIcon(file.name);
  iconEl.style.display = "inline";
  detailEl.innerText = `${file.type || "Unknown type"} • ${formatFileSize(file.size)}`;
}

// ✅ Xử lý Drag & Drop
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

// 🧠 Icon file theo đuôi
function getFileIcon(fileName) {
  const ext = fileName.split('.').pop().toLowerCase();
  switch (ext) {
    case 'enc': return '/static/icons/lock.png';
    case 'key': return '/static/icons/key.png';
    case 'txt': return '/static/icons/txt.png';
    case 'pdf': return '/static/icons/pdf.png';
    default: return '/static/icons/file.png';
  }
}

// 📐 Định dạng dung lượng
function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}
