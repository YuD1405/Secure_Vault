document.addEventListener("DOMContentLoaded", () => {
  const inputs = {
    name: document.getElementById("name"),
    dob: document.getElementById("dob"),
    phone: document.getElementById("phone"),
    address: document.getElementById("address"),
    email: document.getElementById("email"),
    pass1: document.getElementById("passphrase"),
    pass2: document.getElementById("repeat_passphrase"),
  };

  const errors = {
    name: document.getElementById("name-error"),
    dob: document.getElementById("dob-error"),
    phone: document.getElementById("phone-error"),
    address: document.getElementById("address-error"),
    email: document.getElementById("email-error"),
    pass1: document.getElementById("passphrase-error"),
    pass2: document.getElementById("repeat_passphrase-error"),
  };

  const validators = {
    name: (val) => val.trim().length > 0 || "Name is required.",
    dob: (val) => !!val || "Date of birth is required.",
    phone: (val) => /^\d{10}$/.test(val) || "Phone must be 10 digits.",
    address: (val) => val.trim().length > 0 || "Address is required.",
    email: (val) =>
      /^[\w.-]+@[\w.-]+\.\w+$/.test(val) || "Invalid email format.",
    pass1: (val) =>
      (val.length >= 8 &&
        /[A-Z]/.test(val) &&
        /\d/.test(val) &&
        /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(val)) ||
      "Passphrase too weak. At least 8 characters, with uppercase letters, numbers, symbols",
    pass2: () =>
      inputs.pass2.value === inputs.pass1.value || "Passphrases do not match.",
  };

  Object.keys(inputs).forEach((key) => {
    const input = inputs[key];
    const errorSpan = errors[key];
    const validate = () => {
      const result = validators[key](input.value);
      if (result !== true) {
        input.classList.add("error");
        errorSpan.textContent = result;
      } else {
        input.classList.remove("error");
        errorSpan.textContent = "";
      }
    };
    input.addEventListener("blur", validate); // validate on blur
    input.addEventListener("input", validate); // validate on type
    input.addEventListener("paste", (e) => e.preventDefault());
    input.addEventListener("copy", (e) => e.preventDefault());
  });

  // prevent submit if any field invalid
  document.querySelector("form").addEventListener("submit", (e) => {
    let hasError = false;
    Object.keys(inputs).forEach((key) => {
      const input = inputs[key];
      const result = validators[key](input.value);
      if (result !== true) {
        inputs[key].classList.add("error");
        errors[key].textContent = result;
        hasError = true;
      }
    });
    if (hasError) e.preventDefault();
  });
});
