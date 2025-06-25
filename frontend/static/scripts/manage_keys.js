document.addEventListener("DOMContentLoaded", () => {
const sidebar = document.querySelector(".sidebar");
  const mainToggle = document.querySelector(".main");
  const tabToggle = document.querySelector(".tab-pane");

  sidebar.addEventListener("mouseover", () => {
    mainToggle.classList.add("active");
  });

  sidebar.addEventListener("mouseout", () => {
    mainToggle.classList.remove("active");
  });

  const keyData = [
    {
      index: 1,
      private_key_b64: "3fa85f64f1a3b71d...abcde",
      public_key_pem: "MIIBIjANBgkqh...IDAQAB",
      expiry_date: "2025-09-23",
      status: "active"
    },
    {
      index: 2,
      private_key_b64: "7e992a57c30ef1a3...xyz",
      public_key_pem: "MIIBCgKCAQEAr...ABCD",
      expiry_date: "2024-12-31",
      status: "deactivated"
    }
  ];

  const tableBody = document.getElementById("rsa-key-table-body");
  keyData.forEach(key => {
    const row = document.createElement("tr");
    const statusLabel = key.status === 'active'
      ? `<span class="status-badge status-active">Active</span>`
      : `<span class="status-badge status-inactive">Deactivated</span>`;

    row.innerHTML = `
      <td>${key.index}</td>
      <td>${key.private_key_b64.slice(0, 20)}...</td>
      <td>${key.public_key_pem.slice(0, 20)}...</td>
      <td>${key.expiry_date}</td>
      <td>${statusLabel}</td>
      <td>
        ${key.status === "active"
          ? `<button class="deactivate-btn" onclick="deactivateKey(${key.index})">Deactivate</button>`
          : `<em>--</em>`}
      </td>
    `;
    tableBody.appendChild(row);
  });
});

function deactivateKey(index) {
  alert("Bạn vừa nhấn Deactivate key #" + index);
  // Gọi API hoặc cập nhật UI tại đây
}
