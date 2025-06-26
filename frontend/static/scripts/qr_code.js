document.addEventListener("DOMContentLoaded", () => {
  // Load QR như cũ
  fetch("/utils/my_qr_url")
    .then(res => res.json())
    .then(data => {
      if (data.qr_url) {
        document.getElementById("qr-img").src = data.qr_url;
      } else {
        showToast("QR không tồn tại", "error");
      }
    });

  // Bắt sự kiện khi click nút Scan QR
  const decodeBtn = document.getElementById("scan-btn");
  if (decodeBtn) {
    decodeBtn.addEventListener("click", () => {
      const fileInput = document.getElementById("qr_file");
      const file = fileInput.files[0];
      console.log(fileInput);
      if (!file) {
        showToast("Vui lòng chọn ảnh QR để giải mã", "error");
        return;
      }

      const formData = new FormData();
      formData.append("qr_file", file);

      fetch("/utils/decode_qr", {
        method: "POST",
        body: formData
      })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            showToast("Đã thêm người dùng!", "success");
            fileInput.value = "";
            loadOwnedKeys();
          } else {
            showToast(data.message || "Giải mã QR thất bại", "error");
          }
        })
        .catch(err => {
          console.error(err);
          showToast("Lỗi gửi ảnh QR", "error");
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

  if (tabId === "owned-keys") {
    loadOwnedKeys();
  }
}

// Tải ảnh QR
function downloadQR() {
  const qrImg = document.getElementById("qr-img");

  if (!qrImg.src || qrImg.src.includes("undefined") || qrImg.src.trim() === "") {
    showToast("QR chưa được tạo hoặc tải xong!", "error");
    return;
  }

  const link = document.createElement("a");
  link.href = qrImg.src;
  link.download = "my_qr_code.png";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function loadOwnedKeys() {
    const tbody = document.getElementById("owned-keys-tbody");
    if (!tbody) {
      console.warn("Không tìm thấy tbody để render owned keys.");
      return;
    }

    fetch("/utils/owned_keys")
        .then(res => res.json())
        .then(data => {
            console.log(data);
            tbody.innerHTML = "";  

            if (!data.success ) {
                tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;font-style:italic;">No public keys found.</td></tr>`;
                showToast("Bạn chưa có public key nào được lưu.", "info");
                return;
            }

            data.data.forEach((key, index) => {
                const row = document.createElement("tr");
                row.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${key.email}</td>
                    <td>${key.date_added}</td>
                    <td><pre>${key.public_key.slice(0, 40)}...</pre></td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch(err => {
            showToast("Failed to fetch owned keys", "error");
            console.error("Failed to fetch owned keys:", err);
        });
}
