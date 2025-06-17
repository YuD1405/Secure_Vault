async function register() {
  const data = {
    email: document.getElementById("email").value,
    passphrase: document.getElementById("passphrase").value,
  };

  const res = await fetch("http://localhost:5000/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  const result = await res.json();
  document.getElementById("result").innerText = result.message;
}
