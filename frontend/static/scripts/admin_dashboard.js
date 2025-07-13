document.addEventListener("DOMContentLoaded", () => {
  initSearchHandler();  

  const sidebar = document.querySelector(".sidebar");
  const mainToggle = document.querySelector(".main");

  if (sidebar && mainToggle) {
    sidebar.addEventListener("mouseover", () => mainToggle.classList.add("active"));
    sidebar.addEventListener("mouseout", () => mainToggle.classList.remove("active"));
  }

  const $ = document.querySelector.bind(document);
  const $$ = document.querySelectorAll.bind(document);
  const tabActive = $(".tab-item.active");
  const line = $(".tabs .line");

  if (tabActive && line) {
    requestIdleCallback(() => {
      line.style.left = tabActive.offsetLeft + "px";
      line.style.width = tabActive.offsetWidth + "px";
    });
  }

  // Tìm kiếm
  const searchInput = document.querySelector(".input-group input");
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      const searchText = searchInput.value.toLowerCase();
      const table_rows = document.querySelectorAll("tbody tr");

      table_rows.forEach((row, i) => {
        const rowText = row.textContent.toLowerCase();
        const isVisible = rowText.includes(searchText);
        row.classList.toggle("hide", !isVisible);
        row.style.setProperty("--delay", i / 25 + "s");
      });

      document.querySelectorAll("tbody tr:not(.hide)").forEach((row, i) => {
        row.style.backgroundColor = i % 2 === 0 ? "transparent" : "#0000000b";
      });
    });
  }

  // Load logs ngay khi vào
  fetchAndRenderLogs();

  const reloadBtn = document.getElementById("reloadBtn");
  if (reloadBtn) {
    reloadBtn.addEventListener("click", () => {
      fetchAndRenderLogs();
      showToast("Reloaded logs table", "success");
    });
  }

});

// ===== FETCH + RENDER =====
async function fetchAndRenderLogs() {
  try {
    const res = await fetch("/utils/log_security", {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    const logs = await res.json();
    const tbody = document.querySelector("tbody");
    tbody.innerHTML = "";

    logs.forEach((log, index) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${index + 1}</td>
        <td><p class="status ${getStatusClass(log.level)}">${log.level}</p></td>
        <td>${log.timestamp}</td>
        <td>${log.user}</td>
        <td>${log.action}</td>
        <td>${log.status}</td>
        <td style="white-space: pre-wrap">${log.details}</td>
      `;
      tbody.appendChild(tr);
    });

    // Gán lại sự kiện sort
    addSortHandler();
    initSearchHandler();
  } catch (err) {
    console.error("Error loading logs:", err);
    showToast("Fail to reload logs", "error");
  }
}

function getStatusClass(level) {
  switch (level.toUpperCase()) {
    case "INFO": return "info";
    case "WARNING": return "warning";
    case "ERROR": return "error";
    default: return "type1";
  }
}

// ===== SORT TABLE =====
function addSortHandler() {
  const table_headings = document.querySelectorAll("thead th");
  let sort_asc = true;

  table_headings.forEach((head, i) => {
    head.onclick = () => {
      const table_rows = [...document.querySelectorAll("tbody tr")];

      // Reset các tiêu đề khác
      table_headings.forEach(h => h.classList.remove("active"));
      head.classList.add("active");

      // Reset tất cả td và gán active cho cột đang được sort
      document.querySelectorAll("td").forEach(td => td.classList.remove("active"));
      table_rows.forEach(row => {
        const cells = row.querySelectorAll("td");
        if (cells[i]) cells[i].classList.add("active");
      });

      head.classList.toggle("asc", sort_asc);
      sort_asc = head.classList.contains("asc") ? false : true;

      sortTable(i, sort_asc, table_rows);
    };
  });
}

function sortTable(column, sort_asc, rows) {
  const tbody = document.querySelector("tbody");

  rows
    .sort((a, b) => {
      const aText = a.querySelectorAll("td")[column].textContent.toLowerCase();
      const bText = b.querySelectorAll("td")[column].textContent.toLowerCase();

      if (sort_asc) {
        return aText < bText ? 1 : -1;
      } else {
        return aText < bText ? -1 : 1;
      }
    })
    .forEach(row => tbody.appendChild(row));
}

function initSearchHandler() {
  const searchInput = document.querySelector(".input-group input");
  if (!searchInput) return;

  searchInput.addEventListener("input", () => {
    const searchText = searchInput.value.toLowerCase();
    const tableRows = document.querySelectorAll("tbody tr");

    tableRows.forEach((row, i) => {
      const rowText = row.textContent.toLowerCase();
      const isVisible = rowText.includes(searchText);
      row.classList.toggle("hide", !isVisible);
      row.style.setProperty("--delay", i / 25 + "s");
    });

    // Stripe lại sau khi lọc
    document.querySelectorAll("tbody tr:not(.hide)").forEach((row, i) => {
      row.style.backgroundColor = i % 2 === 0 ? "transparent" : "#0000000b";
    });
  });
}
