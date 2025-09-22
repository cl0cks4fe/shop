document.addEventListener('DOMContentLoaded', async () => {
  // Load saved settings
  await loadSettings();

  // Set up event listeners
  document.getElementById('save').addEventListener('click', saveSettings);
  document.getElementById('testConnection').addEventListener('click', testConnection);

  // Auto-save on input changes
  document.getElementById('machineIP').addEventListener('input', debounce(saveSettings, 1000));
  document.getElementById('machinePort').addEventListener('input', debounce(saveSettings, 1000));
  document.getElementById('uploadPath').addEventListener('input', debounce(saveSettings, 1000));
  document.getElementById('autoDetect').addEventListener('change', saveSettings);
});

async function loadSettings() {
  try {
    const result = await browser.storage.sync.get(['machineIP', 'machinePort', 'uploadPath', 'autoDetect']);

    document.getElementById('machineIP').value = result.machineIP || '192.168.1.100';
    document.getElementById('machinePort').value = result.machinePort || '8080';
    document.getElementById('uploadPath').value = result.uploadPath || '/upload';
    document.getElementById('autoDetect').checked = result.autoDetect || false;

    console.log('Settings loaded:', result);
  } catch (error) {
    console.error('Failed to load settings:', error);
    showStatus('Failed to load settings', 'error');
  }
}

async function saveSettings() {
  try {
    const machineIP = document.getElementById('machineIP').value.trim();
    const machinePort = document.getElementById('machinePort').value.trim();
    const uploadPath = document.getElementById('uploadPath').value.trim();
    const autoDetect = document.getElementById('autoDetect').checked;

    // Validate IP address
    if (machineIP && !isValidIP(machineIP)) {
      showStatus('Please enter a valid IP address', 'error');
      return;
    }

    // Validate port
    const port = parseInt(machinePort);
    if (machinePort && (isNaN(port) || port < 1 || port > 65535)) {
      showStatus('Please enter a valid port number (1-65535)', 'error');
      return;
    }

    // Validate upload path
    if (uploadPath && !uploadPath.startsWith('/')) {
      showStatus('Upload path must start with /', 'error');
      return;
    }

    const settings = {
      machineIP: machineIP || '192.168.1.100',
      machinePort: machinePort || '8080',
      uploadPath: uploadPath || '/upload',
      autoDetect: autoDetect
    };

    await browser.storage.sync.set(settings);
    showStatus('Settings saved successfully!', 'success');

    console.log('Settings saved:', settings);
  } catch (error) {
    console.error('Failed to save settings:', error);
    showStatus('Failed to save settings', 'error');
  }
}

async function testConnection() {
  const button = document.getElementById('testConnection');
  const statusElement = document.getElementById('connectionStatus');

  button.disabled = true;
  button.textContent = 'Testing...';
  statusElement.textContent = 'Testing...';
  statusElement.className = 'status-indicator status-testing';

  try {
    const machineIP = document.getElementById('machineIP').value.trim() || '192.168.1.100';
    const machinePort = document.getElementById('machinePort').value.trim() || '8080';
    const uploadPath = document.getElementById('uploadPath').value.trim() || '/upload';

    console.log(`Testing connection to ${machineIP}:${machinePort}${uploadPath}`);

    // Test connection with a simple GET request to ping endpoint
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

    const pingPath = uploadPath.replace('/upload', '/ping') || '/ping';
    const response = await fetch(`http://${machineIP}:${machinePort}${pingPath}`, {
      method: 'GET',
      signal: controller.signal,
      headers: {
        'X-Requested-With': 'VF2Controller-Test'
      }
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      showStatus('Connection successful!', 'success');
      statusElement.textContent = 'Connected';
      statusElement.className = 'status-indicator status-connected';
    } else {
      throw new Error(`Server returned ${response.status}`);
    }

  } catch (error) {
    console.error('Connection test failed:', error);

    let errorMessage = 'Connection failed';
    if (error.name === 'AbortError') {
      errorMessage = 'Connection timeout';
    } else if (error.message.includes('fetch')) {
      errorMessage = 'Network error - check IP and port';
    }

    showStatus(errorMessage, 'error');
    statusElement.textContent = 'Disconnected';
    statusElement.className = 'status-indicator status-disconnected';
  } finally {
    button.disabled = false;
    button.textContent = 'Test Connection';
  }
}

function isValidIP(ip) {
  const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
  return ipRegex.test(ip);
}

function showStatus(message, type) {
  const statusElement = document.getElementById('status');
  statusElement.textContent = message;
  statusElement.className = `status status-${type}`;

  // Auto-clear status after 3 seconds for success/error messages
  if (type === 'success' || type === 'error') {
    setTimeout(() => {
      statusElement.textContent = '';
      statusElement.className = 'status';
    }, 3000);
  }
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
