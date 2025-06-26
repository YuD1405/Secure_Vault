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

  // 📦 3. Gán DOM cho 2 file input: file và chữ ký
  const dropFile = document.getElementById("drop-file");
  const dropSig = document.getElementById("drop-signature");
  const fileInput = document.getElementById("file-upload");
  const sigInput = document.getElementById("sig-upload");

  const fileDisplay = document.getElementById("file-upload-show");
  const fileIcon = document.getElementById("file-icon");
  const fileDetails = document.getElementById("file-details-verify");

  const sigDisplay = document.querySelectorAll("#file-upload-show")[1];
  const sigIcon = document.querySelectorAll("#file-icon")[1];
  const sigDetails = document.getElementById("file-details-sig");

  const form = document.getElementById("uploadForm");
  const resultDisplay = document.getElementById("uploadResult");

  if (!dropFile || !dropSig || !fileInput || !sigInput || !form) return;

  // 📁 Hiển thị thông tin file helper
  function updatePreview(file, displayEl, iconEl, detailEl) {
    if (!file) return;
    displayEl.value = file.name;
    iconEl.src = getFileIcon(file.name);
    iconEl.style.display = "inline";
    detailEl.innerText = `${file.type || "Unknown type"} • ${formatFileSize(file.size)}`;
  }

  // 🖱️ Khi chọn file bằng tay
  fileInput.addEventListener("change", function () {
    const file = this.files[0];
    updatePreview(file, fileDisplay, fileIcon, fileDetails);
  });

  sigInput.addEventListener("change", function () {
    const file = this.files[0];
    updatePreview(file, sigDisplay, sigIcon, sigDetails);
  });

  // 📤 Submit xác minh chữ ký
  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const file = fileInput.files[0];
    const sig = sigInput.files[0];
    const pubKey = document.getElementById("public_key_selector").value;

    if (!file || !sig || !pubKey) {
      showToast("Vui lòng chọn đầy đủ file, chữ ký và public key!", "error");
      return;
    }

    const formData = new FormData();
    formData.append("file_to_verify", file);
    formData.append("signature", sig);
    formData.append("public_key_path", pubKey);

    try {
      const res = await fetch("/utils/verify_signature", {
        method: "POST",
        body: formData,
      });
      const result = await res.json();
      if (result.error) {
        showToast(result.error, "error");
      } else {
        showToast(result.message || "Xác minh thành công!", "success");
      }
    } catch (err) {
      console.error(err);
      showToast("Lỗi khi gửi xác minh", "error");
    }
  });

  // 🖱️ Drag & Drop cho cả 2 khung
  function setupDropEvents(area, inputEl, displayEl, iconEl, detailEl) {
    ["dragenter", "dragover", "dragleave", "drop"].forEach(eventName => {
      area.addEventListener(eventName, e => {
        e.preventDefault();
        e.stopPropagation();
      });
    });

    ["dragenter", "dragover"].forEach(eventName => {
      area.addEventListener(eventName, () => area.classList.add("highlight"));
    });

    ["dragleave", "drop"].forEach(eventName => {
      area.addEventListener(eventName, () => area.classList.remove("highlight"));
    });

    area.addEventListener("drop", e => {
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        inputEl.files = files;
        updatePreview(files[0], displayEl, iconEl, detailEl);
      }
    });
  }

  setupDropEvents(dropFile, fileInput, fileDisplay, fileIcon, fileDetails);
  setupDropEvents(dropSig, sigInput, sigDisplay, sigIcon, sigDetails);
});

// ⚙️ Format dung lượng file
function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  else if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  else return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

// 🧠 Chọn icon file dựa theo phần mở rộng
function getFileIcon(fileName) {
  const ext = fileName.split('.').pop().toLowerCase();
  switch (ext) {
    case 'pdf': 
        return '/static/icons/pdf.png';
    case 'doc':
    case 'docx': 
        return '/static/icons/doc.png';
    case 'sig': 
        return '/static/icons/sig.png';
    case 'txt': 
        return '/static/icons/txt.png';
    default: 
        return '/static/icons/file.png';
  }
}