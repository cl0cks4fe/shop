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
    msg.style.display = 'none';

    fetch('api/upload', { method: 'POST', body: new FormData(form) })
        .then(r => r.json().then(data => ({ ok: r.ok, data })))
        .then(({ ok, data }) => {
            if (!ok) {
                showMsg(data.error || 'Upload failed', 'error');
                btn.disabled = false;
                return;
            }
            pollTransferStatus();
        })
        .catch(() => {
            showMsg('Network error', 'error');
            btn.disabled = false;
        });
});

function pollTransferStatus() {
    showMsg('Transferring... ', 'info');
    let interval = setInterval(() => {
        fetch('api/status')
            .then(r => r.json())
            .then(status => {
                if (!status.active_transfer) {
                    clearInterval(interval);
                    showMsg('Transfer complete!', 'success');
                    btn.disabled = false;
                form.reset()
                }
            })
            .catch(() => {
                clearInterval(interval);
                showMsg('Network error during transfer', 'error');
                btn.disabled = false;
                form.reset()
            });
    }, 1000);
}
