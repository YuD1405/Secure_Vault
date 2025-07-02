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
          showToast(data.message || "Không thể tải danh sách khóa", "error");
        }
      })
      .catch(err => {
        console.error("❌ Lỗi khi load key list:", err);
        showToast("Không thể kết nối máy chủ", "error");
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

      row.innerHTML = `
        <td>${index + 1}</td>
        <td>${key.private_key_b64.slice(0, 20)}...</td>
        <td>${key.public_key_pem.slice(0, 20)}...</td>
        <td>${expiryDate}</td>
        <td>${statusLabel}</td>
      `;

      tableBody.appendChild(row);
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
            showToast(data.message || "Tạo khóa thành công!", "success");
            loadKeyList(); // reload lại bảng
          } else {
            showToast(data.message || "Tạo khóa thất bại", "error");
          }
        })
        .catch(err => {
          console.error("❌ Lỗi khi tạo khóa:", err);
          showToast("Không thể tạo khóa mới", "error");
        });
    });
  }

  loadKeyList();
});
