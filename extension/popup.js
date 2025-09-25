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
  const pingBtn = document.getElementById('pingBtn');
  
  // Disable button and show attempting state
  pingBtn.disabled = true;
  pingBtn.textContent = 'Connecting...';

  try {
    // Add timeout to the fetch request
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
    
    const response = await fetch(`http://${host}:${port}/ping`, {
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (response.ok) {
      showStatus('Connected!', 'success');
    } else {
      showStatus(`Error: ${response.status} ${response.statusText}`, 'error');
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      showStatus('Connection timeout!', 'error');
    } else {
      showStatus('Connection failed!', 'error');
    }
  } finally {
    // Re-enable button and restore original text
    pingBtn.disabled = false;
    pingBtn.textContent = 'Ping Server';
  }
};

// Show status message
function showStatus(message, type) {
  const status = document.getElementById('status');
  status.textContent = message;
  status.className = `status ${type}`;
  
  // Clear status after delay, but only for success/error messages
  if (type === 'success' || type === 'error') {
    setTimeout(() => {
      status.textContent = '';
      status.className = ''; // Clear all classes
    }, 3000);
  }
}
