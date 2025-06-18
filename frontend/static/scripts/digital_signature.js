document.getElementById('uploadForm').addEventListener('submit', async (event) => {
  event.preventDefault();  // Ngừng việc gửi form mặc định

  const formData = new FormData();
  formData.append('file', document.querySelector('[name="file"]').files[0]);

  const res = await fetch('/utils/signing_file', {
    method: 'POST',
    body: formData,
  });

  const result = await res.json();
  document.getElementById('uploadResult').innerText = result.message;
});

document.getElementById('verifyForm').addEventListener('submit', async (event) => {
  event.preventDefault();  // Ngừng việc gửi form mặc định

  const formData = new FormData();
  formData.append('file', document.querySelector('[name="file"]').files[0]);
  formData.append('signature', document.querySelector('[name="signature"]').files[0]);
  formData.append('public_key_path', document.querySelector('[name="public_key_path"]').value);

  const res = await fetch('/utils/verify_signature', {
    method: 'POST',
    body: formData,
  });

  const result = await res.json();
  document.getElementById('verifyResult').innerText = result.message;
});
