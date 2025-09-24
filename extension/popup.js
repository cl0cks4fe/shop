/* Popup Script - Extension Settings */

// Load saved settings
chrome.storage.sync.get(['host', 'port'], (result) => {
  document.getElementById('host').value = result.host || 'test.local';
  document.getElementById('port').value = result.port || '3000';
});

// Get current form values
function getCurrentSettings() {
  return {
    host: document.getElementById('host').value || 'test.local',
    port: document.getElementById('port').value || '3000'
  };
}

// Save settings button
document.getElementById('saveBtn').onclick = () => {
  const { host, port } = getCurrentSettings();
  chrome.storage.sync.set({ host, port });
  showStatus('Saved!', 'success');
};

// Ping server button
document.getElementById('pingBtn').onclick = async () => {
  const { host, port } = getCurrentSettings();

  try {
    const response = await fetch(`http://${host}:${port}/ping`);
    showStatus(response.ok ? 'Connected!' : 'Error!', response.ok ? 'success' : 'error');
  } catch (error) {
    showStatus('Failed!', 'error');
  }
};

// Show status message
function showStatus(message, type) {
  const status = document.getElementById('status');
  status.textContent = message;
  status.className = `status ${type}`;
  setTimeout(() => status.textContent = '', 2000);
}
