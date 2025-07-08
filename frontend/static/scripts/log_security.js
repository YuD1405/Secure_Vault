document.getElementById("refreshBtn").addEventListener("click", async () => {
  try {
    const res = await fetch("/utils/log_security");
    const html = await res.text();

    // Lấy phần bảng mới ra khỏi response
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    const newTable = doc.querySelector("#logContainer");

    // Thay thế bảng cũ
    document.getElementById("logContainer").innerHTML = newTable.innerHTML;
  } catch (err) {
    showToast("Error while reloading the log table!");
    console.error(err);
  }
});
