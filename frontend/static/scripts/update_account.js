document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(".update-form");

    function fetchUserInfo() {
        fetch("/auth/user_info")
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    showToast("Failed to load user info", "error");
                    return;
                }
                document.getElementById("name").value = data.fullname || "";
                document.getElementById("dob").value = data.dob || "";
                document.getElementById("address").value = data.address || "";
                document.getElementById("phone").value = data.phone || "";
                document.getElementById("email").value = data.email || "";
            })
            .catch(err => {
                console.error(err);
                showToast("Error loading user info", "error");
            });
    }

    // Gọi khi trang load
    fetchUserInfo();

    // Gửi form bằng fetch
    form.addEventListener("submit", function (e) {
        e.preventDefault();
        const formData = new FormData(form);

        fetch("/auth/update_account", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast("Thông tin đã được cập nhật!", "success");
                fetchUserInfo(); // 👈 tự fetch lại để hiển thị dữ liệu mới nhất
            } else {
                showToast(data.message || "Cập nhật thất bại", "error");
            }
        })
        .catch(err => {
            console.error(err);
            showToast("Lỗi khi gửi dữ liệu", "error");
        });
    });

    // Sidebar hover
    const sidebar = document.querySelector(".sidebar");
    const mainToggle = document.querySelector(".main");

    sidebar.addEventListener("mouseover", () => {
        mainToggle.classList.add("active");
    });

    sidebar.addEventListener("mouseout", () => {
        mainToggle.classList.remove("active");
    });
});
