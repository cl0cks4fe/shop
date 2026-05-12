const form = document.getElementById('sendForm');
const msg = document.getElementById('message');
const btn = document.getElementById('sendBtn');

function showMsg(text, cls) {
    msg.textContent = text;
    msg.className = 'flash-message ' + cls;
    msg.style.display = 'block';
}

form.addEventListener('submit', function(e) {
    e.preventDefault();
    btn.disabled = true;
    showMsg('Transferring... ', 'info');

    fetch('api/upload', { method: 'POST', body: new FormData(form) })
        .then(r => r.json().then(data => ({ ok: r.ok, data })))
        .then(({ ok, data }) => {
            if (!ok) {
                showMsg(data.error || 'Upload failed', 'error');
            } else {
                showMsg('Transfer complete!', 'success');
            }
        })
        .catch(() => {
            showMsg('Network error', 'error');
        })
        .finally(() => {
            btn.disabled = false;
        });
});
