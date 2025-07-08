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
        //const expiry = key.expiry_date?.split("T")[0] || "Chưa có";
       const trimmedKey = trimPublicKey(key.public_key_pem || key.public_key || "");

        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${index + 1}</td>
          <td>${email}</td>
          <td>${created}</td>
          <td><pre title="${trimmedKey}">${trimmedKey.slice(0, 40)}...</pre></td>
        `;
        tbody.appendChild(row);
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
    const pubkey = row.children[3].textContent.toLowerCase();
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