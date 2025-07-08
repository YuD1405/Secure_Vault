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

      const statusLabel = key.status === 'active'
        ? `<span class="status-badge status-active">Active</span>`
        : `<span class="status-badge status-inactive">Deactivated</span>`;

      const expiryDate = key.expiry_date.split("T")[0];

      // Tạo ô Private Key với nút copy icon SVG
      const privateKeyCell = document.createElement("td");
      privateKeyCell.innerHTML = `
        <div class="key-cell">
          <code class="private-key">${key.private_key_b64.slice(0, 20)}...</code>
          <button class="copy-btn" data-key="${key.private_key_b64}" title="Copy Private Key" aria-label="Copy Private Key">
            <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 16 16" width="16" height="16">
              <path d="M10 1.5A1.5 1.5 0 0 1 11.5 3v8A1.5 1.5 0 0 1 10 12.5H4A1.5 1.5 0 0 1 2.5 11V3A1.5 1.5 0 0 1 4 1.5h6zM4 2a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V3a1 1 0 0 0-1-1H4z"/>
              <path d="M5 5h5v1H5V5zM5 7h5v1H5V7z"/>
            </svg>
          </button>
        </div>
      `;

      // Tạo ô Public Key với nút copy icon SVG
      const publicKeyCell = document.createElement("td");
      publicKeyCell.innerHTML = `
        <div class="key-cell">
          <code class="public-key">${key.public_key_pem.slice(0, 20)}...</code>
          <button class="copy-btn" data-key="${key.public_key_pem}" title="Copy Public Key" aria-label="Copy Public Key">
            <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 16 16" width="16" height="16">
              <path d="M10 1.5A1.5 1.5 0 0 1 11.5 3v8A1.5 1.5 0 0 1 10 12.5H4A1.5 1.5 0 0 1 2.5 11V3A1.5 1.5 0 0 1 4 1.5h6zM4 2a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V3a1 1 0 0 0-1-1H4z"/>
              <path d="M5 5h5v1H5V5zM5 7h5v1H5V7z"/>
            </svg>
          </button>
        </div>
      `;

      // Tạo các ô còn lại
      const indexCell = document.createElement("td");
      indexCell.textContent = index + 1;

      const expiryCell = document.createElement("td");
      expiryCell.textContent = expiryDate;

      const statusCell = document.createElement("td");
      statusCell.innerHTML = statusLabel;

      // Append các ô vào row
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

  loadKeyList();
});
