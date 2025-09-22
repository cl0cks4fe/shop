/**
 * POPUP SCRIPT - Extension Settings Interface
 * 
 * Handles the extension popup that appears when clicking the extension icon.
 * Provides UI for configuring server connection settings and testing connectivity.
 * 
 * Features:
 * - Load/save host and port settings to browser storage
 * - Ping server to test connectivity 
 * - Visual feedback for user actions
 */

/**
 * INITIALIZATION - Load saved settings from storage
 * Retrieves previously saved host/port settings and populates the form fields.
 * Uses defaults (test.local:3000) if no settings exist.
 */
chrome.storage.sync.get(['host', 'port'], (result) => {
  document.getElementById('host').value = result.host || 'test.local';
  document.getElementById('port').value = result.port || '3000';
});

/**
 * GET CURRENT SETTINGS
 * Extracts host/port values from form with defaults.
 */
function getCurrentSettings() {
  return {
    host: document.getElementById('host').value || 'test.local',
    port: document.getElementById('port').value || '3000'
  };
}

/**
 * SAVE SETTINGS HANDLER
 * Saves the current host/port values to browser storage.
 */
document.getElementById('saveBtn').onclick = () => {
  const { host, port } = getCurrentSettings();
  chrome.storage.sync.set({ host, port });
  showStatus('Saved!', 'success');
};

/**
 * PING SERVER HANDLER
 * Tests connectivity to the configured server.
 */
document.getElementById('pingBtn').onclick = async () => {
  const { host, port } = getCurrentSettings();
  
  try {
    const response = await fetch(`http://${host}:${port}/ping`);
    showStatus(response.ok ? 'Connected!' : 'Error!', response.ok ? 'success' : 'error');
  } catch (error) {
    showStatus('Failed!', 'error');
  }
};

/**
 * STATUS MESSAGE DISPLAY
 * Shows temporary status messages to the user with color coding.
 * Messages auto-hide after 2 seconds to keep UI clean.
 * 
 * @param {string} message - Text to display to user
 * @param {string} type - 'success' or 'error' for styling
 */
function showStatus(message, type) {
  const status = document.getElementById('status');
  status.textContent = message;
  status.className = `status ${type}`;
  setTimeout(() => status.textContent = '', 2000);
}
