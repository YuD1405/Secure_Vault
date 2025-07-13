document.addEventListener("DOMContentLoaded", () => {
  // 📦 Sidebar hover mở rộng main
  const sidebar = document.querySelector(".sidebar");
  const mainToggle = document.querySelector(".main");

  sidebar.addEventListener("mouseover", () => mainToggle.classList.add("active"));
  sidebar.addEventListener("mouseout", () => mainToggle.classList.remove("active"));

  // 🔑 Gọi API để lấy danh sách khoá và render bảng
  function loadKeyList() {
    fetch("/crypto/manage_keys")
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          renderKeyTable(data.keys);
        } else {
          showToast(data.message || "Unable to load key list.", "error");
        }
      })
      .catch(err => {
        console.error("Lỗi khi load key list:", err);
        showToast("Unable to connect to the server.", "error");
      });
  }

  // 📋 Render bảng hiển thị danh sách khóa
  function renderKeyTable(keys) {
    const tableBody = document.getElementById("rsa-key-table-body");
    tableBody.innerHTML = ""; // Xoá bảng cũ nếu có

    keys.slice().reverse().forEach((key, index) => {
      const row = document.createElement("tr");

      const expiryDateStr = key.expiry_date.split("T")[0];
      const expiryDate = new Date(expiryDateStr);
      const today = new Date();
      today.setHours(0, 0, 0, 0); // reset giờ về 0h00

      // Tính số ngày còn lại
      const timeDiff = expiryDate.getTime() - today.getTime();
      const daysLeft = Math.ceil(timeDiff / (1000 * 60 * 60 * 24));

      // 👉 Xác định trạng thái theo thời gian
      let statusLabel = "";
      if (key.status === 'active') {
        if (daysLeft === 1) {
          statusLabel = `<span class="status-badge status-soon">Expired Soon</span>`;
        } else {
          statusLabel = `<span class="status-badge status-active">Active</span>`;
        }
      } else {
        statusLabel = `<span class="status-badge status-inactive">Deactivated</span>`;
      }

      // Cell cho Private Key
      const privateKeyCell = document.createElement("td");
      privateKeyCell.innerHTML = `
        <div class="key-cell">
          <code class="private-key">${key.private_key_b64.slice(0, 20)}...</code>
          <button class="copy-btn" data-key="${key.private_key_b64}" title="Copy Private Key" aria-label="Copy Private Key">
            <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 16 16">
              <path d="M10 1.5A1.5 1.5 0 0 1 11.5 3v1h-1V3a.5.5 0 0 0-.5-.5H3A.5.5 0 0 0 2.5 3v8a.5.5 0 0 0 .5.5h1v1h-1A1.5 1.5 0 0 1 1.5 11V3A1.5 1.5 0 0 1 3 1.5h7z"/>
              <path d="M5 4.5A1.5 1.5 0 0 0 3.5 6v7A1.5 1.5 0 0 0 5 14.5h7a1.5 1.5 0 0 0 1.5-1.5V6A1.5 1.5 0 0 0 12 4.5H5zm-1 1.5A.5.5 0 0 1 4.5 5H12a.5.5 0 0 1 .5.5v7a.5.5 0 0 1-.5.5H5a.5.5 0 0 1-.5-.5V6z"/>
            </svg>
          </button>
        </div>
      `;

      // Cell cho Public Key
      const publicKeyCell = document.createElement("td");
      publicKeyCell.innerHTML = `
        <div class="key-cell">
          <code class="public-key">${key.public_key_pem.slice(0, 20)}...</code>
          <button class="copy-btn" data-key="${key.public_key_pem}" title="Copy Public Key" aria-label="Copy Public Key">
            <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 16 16">
              <path d="M10 1.5A1.5 1.5 0 0 1 11.5 3v1h-1V3a.5.5 0 0 0-.5-.5H3A.5.5 0 0 0 2.5 3v8a.5.5 0 0 0 .5.5h1v1h-1A1.5 1.5 0 0 1 1.5 11V3A1.5 1.5 0 0 1 3 1.5h7z"/>
              <path d="M5 4.5A1.5 1.5 0 0 0 3.5 6v7A1.5 1.5 0 0 0 5 14.5h7a1.5 1.5 0 0 0 1.5-1.5V6A1.5 1.5 0 0 0 12 4.5H5zm-1 1.5A.5.5 0 0 1 4.5 5H12a.5.5 0 0 1 .5.5v7a.5.5 0 0 1-.5.5H5a.5.5 0 0 1-.5-.5V6z"/>
            </svg>
          </button>
        </div>
      `;

      const indexCell = document.createElement("td");
      indexCell.textContent = index + 1;

      const expiryCell = document.createElement("td");
      expiryCell.textContent = expiryDateStr;

      const statusCell = document.createElement("td");
      statusCell.innerHTML = statusLabel;

      row.appendChild(indexCell);
      row.appendChild(privateKeyCell);
      row.appendChild(publicKeyCell);
      row.appendChild(expiryCell);
      row.appendChild(statusCell);

      tableBody.appendChild(row);
    });

    // Gắn sự kiện copy cho nút copy vừa tạo
    tableBody.querySelectorAll(".copy-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const keyToCopy = btn.getAttribute("data-key");
        if (!keyToCopy) return;

        navigator.clipboard.writeText(keyToCopy).then(() => {
          showToast("Copied to clipboard!", "success");
        }).catch(() => {
          showToast("Copy failed! Please copy manually.", "error");
        });
      });
    });

        // Gắn sự kiện click vào từng hàng
    tableBody.querySelectorAll("tr").forEach((row, i) => {
      row.addEventListener("click", () => {
        const key = keys[keys.length - 1 - i]; // vì bạn đang reverse()
        showKeyPopup(key);
      });
    });
  }


  // ➕ Tạo khoá mới khi click nút
  const createKeyBtn = document.getElementById("create-key-btn");
  if (createKeyBtn) {
    createKeyBtn.addEventListener("click", () => {
      fetch("/crypto/regenerate_key", { method: "POST" })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            showToast(data.message || "Key generated successfully!", "success");
            loadKeyList(); // reload lại bảng
          } else {
            showToast(data.message || "Key generation failed.", "error");
          }
        })
        .catch(err => {
          console.error( "Error during key generation:", err);
          showToast("Unable to generate new key.", "error");
        });
    });
  }

  function showKeyPopup(key) {
    const popup = document.getElementById("key-popup");
    const statusSpan = document.getElementById("popup-status");
    const expirySpan = document.getElementById("popup-expiry");
    const extendSection = document.getElementById("extend-section");

    statusSpan.textContent = key.status === 'active' ? 'Active' : 'Deactivated';
    expirySpan.textContent = key.expiry_date.split("T")[0];

    const isActive = key.status === 'active';
    extendSection.style.display = isActive ? "block" : "none";

    if (isActive) {
      document.getElementById("confirm-extend-btn").onclick = () => {
        const days = parseInt(document.getElementById("days-to-extend").value);
        if (isNaN(days) || days <= 0) {
          showToast("Please enter a valid number of days.", "error");
          return;
        }

        fetch("/crypto/extend_key", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: key.email, days_to_add: days })
        })
          .then(res => res.json())
          .then(data => {
            if (data.success) {
              showToast(data.message || "Key successfully extended!", "success");
              closePopup();
              loadKeyList(); 
            } else {
              showToast(data.message || "Extension failed.", "error");
            }
          });
      };

    }

    popup.classList.remove("hidden");
  }
  loadKeyList();
});


function closePopup() {
  document.getElementById("key-popup").classList.add("hidden");
}

