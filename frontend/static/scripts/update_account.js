document.addEventListener("DOMContentLoaded", () => {
    fetch("/auth/user_info")
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                showToast("Failed to load user info");
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
            showToast("Error loading user info");
        });
        
  const sidebar = document.querySelector(".sidebar");
  const mainToggle = document.querySelector(".main");
  const tabToggle = document.querySelector(".tab-pane");

  sidebar.addEventListener("mouseover", () => {
    mainToggle.classList.add("active");
  });

  sidebar.addEventListener("mouseout", () => {
    mainToggle.classList.remove("active");
  });

});

