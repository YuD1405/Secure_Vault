document.getElementById('recovery-form').addEventListener('submit', async function (e) {
  e.preventDefault();

  const email = document.getElementById('email').value.trim();
  const recoveryCode = document.getElementById('recovery-code').value.trim();

  try {
    const response = await fetch('/auth/verify_recovery', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, recovery_code: recoveryCode })
    });

    const result = await response.json();

    if (response.ok && result.success) {
      document.getElementById('step-recovery').style.display = 'none';
      document.getElementById('step-reset').style.display = 'block';
      showToast('Valid recovery code', "success");
    } else {
      showToast(result.message || 'Invalid recovery code', "error");
      // alert(result.message || 'Invalid recovery code');
    }

  } catch (err) {
    console.error(err);
    showToast('Something went wrong while verifying.', "error");
    // alert('Something went wrong while verifying.');
  }
});


document.getElementById('reset-form').addEventListener('submit', async function (e) {
  e.preventDefault();

  const pass1 = document.getElementById('new-password').value;
  const pass2 = document.getElementById('confirm-password').value;
  const email = document.getElementById('email').value;  // 👈 lấy lại email từ form cũ

  if (pass1 !== pass2) {
    showToast('Passwords do not match', "error");
    // alert('Passwords do not match');
    return;
  }

  try {
    const response = await fetch('/auth/reset_password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, new_password: pass1 })
    });

    const result = await response.json();

    if (response.ok && result.success) {
      showToast('Passwords reset successfully!', "success");
      // alert('Password reset successfully!');
      setTimeout(() => {
        window.location.href = "/auth/login";
      }, 3000);
    } else {
      showToast(result.message || 'Reset failed', "error");
      // alert(result.message || 'Reset failed');
    }

  } catch (err) {
    console.error(err);
    showToast('Error resetting password', "error");
    // alert('Error resetting password');
  }
});
