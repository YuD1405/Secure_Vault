document.addEventListener("DOMContentLoaded", () => {
  loadRecipientEmails();
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
    const recipientEmail = document.getElementById("recipient-email")?.value || "hihihi@gmail.com";
    const encryptMode = document.querySelector('input[name="save_format"]:checked')?.value || "combined";

    // ✅ Kiểm tra đủ thông tin
    if (!file) {
      showToast("Please select a file to encrypt!", "error");
      return;
    }

    if (!recipientEmail) {
      showToast("Please select a recipient!", "error");
      return;
    }

    // ✅ Tạo formData
    const formData = new FormData();
    formData.append("file_to_encrypt", file);
    formData.append("output_option", encryptMode);
    formData.append("recipient_email", recipientEmail);

    try {
      const res = await fetch("/crypto/encrypt_file", {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        const errorText = await res.text();
        showToast("Lỗi mã hóa: " + errorText, "error");
        return;
      }

      // 📥 Lấy tên file từ header (nếu có)
      const disposition = res.headers.get("Content-Disposition");
      let filename = "encrypted_file";

      if (disposition && disposition.includes("filename=")) {
        const match = disposition.match(/filename="?([^"]+)"?/);
        if (match) {
          filename = match[1];
        }
      }

      // 📦 Lấy phần mở rộng
      const fileExt = filename.split('.').pop().toLowerCase();

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      // ✅ Tuỳ theo định dạng file → hiển thị Toast tương ứng
      if (fileExt === "zip") {
        showToast(`🔐 File đã được mã hoá và tách khóa. Đã tải: ${filename}`, "success");
      } else if (fileExt === "enc") {
        showToast(`🔐 File đã được mã hoá và gộp thành 1 file. Đã tải: ${filename}`, "success");
      } else {
        showToast(`📁 File mã hoá đã được tải về: ${filename}`, "success");
      }

    } catch (err) {
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

function loadRecipientEmails() {
  const select = document.getElementById("recipient-email");
  if (!select) {
    console.warn("Không tìm thấy #recipient-email để render contact.");
    return;
  }

  fetch("/utils/owned_keys")
    .then(res => res.json())
    .then(data => {
      if (!data.success || !data.data || data.data.length === 0) {
        showToast("Không có người dùng nào trong danh bạ.", "info");
        return;
      }

      // Xoá hết options cũ, giữ lại option đầu tiên
      const placeholder = select.querySelector("option[value='']");
      select.innerHTML = "";
      if (placeholder) select.appendChild(placeholder);

      data.data.forEach((key) => {
        const email = key.owner_email || key.email;
        if (!email) return;

        const option = document.createElement("option");
        option.value = email;
        option.textContent = email;
        select.appendChild(option);
      });
    })
    .catch(error => {
      console.error("❌ Lỗi khi load recipient emails:", error);
      showToast("Không thể tải danh bạ.", "error");
    });
}