document.addEventListener("DOMContentLoaded", () => {
  document.getElementById('scan-input-wrapper').addEventListener('click', () => {
    document.getElementById('qr_file').click();
  });

  document.getElementById('qr_file').addEventListener('change', (e) => {
    const fileName = e.target.files.length ? e.target.files[0].name : 'No file selected';
    document.getElementById('file-name').textContent = fileName;
  });

  // Load QR như cũ
  fetch("/utils/my_qr_url")
    .then(res => res.json())
    .then(data => {
      if (data.qr_url) {
        document.getElementById("qr-img").src = data.qr_url;
      } else {
        showToast("QR code does not exist.", "error");
      }
    });

  // Bắt sự kiện khi click nút Scan QR
  const decodeBtn = document.getElementById("scan-btn");
  if (decodeBtn) {
    decodeBtn.addEventListener("click", () => {
      const fileInput = document.getElementById("qr_file");
      const file = fileInput.files[0];

      if (!file) {
        showToast("Please select a QR image to decode", "error");
        return;
      }

      const formData = new FormData();
      formData.append("qr_code_file", file);

      fetch("/utils/decode_qr", {
        method: "POST",
        body: formData
      })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            showToast(data.message, "success");
            fileInput.value = "";
            loadOwnedKeys();
          } else {
            showToast(data.message || "Failed to decode QR code", "error");
          }
        })
        .catch(err => {
          console.error(err);
          showToast("Failed to upload QR image", "error");
        });
    });

  }

  // Sidebar hover
  const sidebar = document.querySelector(".sidebar");
  const mainToggle = document.querySelector(".main");
  sidebar.addEventListener("mouseover", () => mainToggle.classList.add("active"));
  sidebar.addEventListener("mouseout", () => mainToggle.classList.remove("active"));
});

// Chuyển tab giữa 3 vùng nội dung
function switchTab(tabElement, tabId) {
  document.querySelectorAll(".tab-item").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

  tabElement.classList.add("active");
  document.getElementById(tabId).classList.add("active");

  if (tabId === "lookup") {
    document.getElementById('file-name').textContent = "No file selected";
  }

  if (tabId === "owned-keys") {
    loadOwnedKeys();
  }
}

// Tải ảnh QR
function downloadQR() {
  const qrImg = document.getElementById("qr-img");

  if (!qrImg.src || qrImg.src.includes("undefined") || qrImg.src.trim() === "") {
    showToast("QR code has not been created or loaded!", "error");
    return;
  }

  const link = document.createElement("a");
  link.href = qrImg.src;
  link.download = "my_qr_code.png";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// Hàm fetch chuẩn
function loadOwnedKeys() {
  const tbody = document.getElementById("owned-keys-tbody");
  if (!tbody) {
    console.log("Không tìm thấy tbody để render owned keys.");
    return;
  }

  fetch("/utils/owned_keys")
    .then(res => res.json())
    .then(data => {
      const qrWrapper = document.getElementById("scanned-qr-wrapper");
      const qrImg = document.getElementById("scanned-qr-img");
      tbody.innerHTML = "";
      const container = document.getElementById("active-key-info");

      if (!data.success || !data.data || data.data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;font-style:italic;">No public keys have been saved.</td></tr>`;
        showToast("You have no saved public keys.", "info");
        return;
      }

      data.data.forEach((key, index) => {
        const email = key.owner_email || "-";
        const created = key.creation_date?.split("T")[0] || "-";
        const expiry = key.expiry_date?.split("T")[0] || "-";
        const trimmedKey = trimPublicKey(key.public_key_pem || key.public_key || "");
        const qrImage = key.qr_image || null;

        let status = "Unknown";
        if (expiry !== "-") {
          const today = new Date();
          const expiryDate = new Date(expiry);
          const diffMs = expiryDate - today;
          const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

          if (diffDays < 0) {
            status = "Expired";
          } else if (diffDays <= 1) {
            status = "Expiring Soon";
          } else {
            status = "Valid";
          }
        }

        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${index + 1}</td>
          <td>${email}</td>
          <td>${created}</td>
          <td>${expiry}</td>
          <td><pre title="${trimmedKey}" data-pubkey="${trimmedKey}">${trimmedKey.slice(0, 40)}...</pre></td>
        `;
        const statusCell = document.createElement("td");
        const statusSpan = document.createElement("span");
        statusSpan.classList.add("status-label");

        if (status === "Expired") {
          statusSpan.classList.add("status-expired");
          statusSpan.textContent = "Expired";
        } else if (status === "Expiring Soon") {
          statusSpan.classList.add("status-warning");
          statusSpan.textContent = "Expiring Soon";
        } else {
          statusSpan.classList.add("status-valid");
          statusSpan.textContent = "Valid";
        }

        statusCell.appendChild(statusSpan);
        row.appendChild(statusCell);
        tbody.appendChild(row);

        row.addEventListener("click", () => {
          if (qrImage) {
            document.getElementById("qr-modal-img").src = qrImage;
            document.getElementById("qr-modal").style.display = "flex";

            // ✅ cập nhật href cho nút download
            const downloadBtn = document.getElementById("download-qr-btn");
            downloadBtn.href = qrImage;
            downloadBtn.download = `${email}_qr.png`;  // optional: đổi tên file theo email
          } else {
            showToast("QR code not available for this key.", "warning");
          }
        });
      });
    })
    .catch(error => {
      console.error("Lỗi khi load owned keys:", error);
      tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:red;">Failed to load the list of public keys.</td></tr>`;
      showToast("Cannot connect to the server", "error");
    });
}


function filterPublicKeys() {
  const keyword = document.getElementById('search-publickey').value.toLowerCase();
  const rows = document.querySelectorAll('#owned-keys-tbody tr');  
  rows.forEach(row => {
    const email = row.children[1].textContent.toLowerCase();
    const pubkey = row.children[4].querySelector('pre').dataset.pubkey.toLowerCase();
    const match = email.includes(keyword) || pubkey.includes(keyword);
    row.style.display = match ? '' : 'none';
  });
}

function trimPublicKey(pem) {
  if (!pem) return "";
  return pem
    .split('\n')
    .filter(line => !line.includes("-----"))
    .join('');
}

function closeQRModal() {
  document.getElementById("qr-modal").style.display = "none";
}
