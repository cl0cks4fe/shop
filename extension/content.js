/* Content Script - Google Drive Integration */

let lastClickedFile = null;
const buttonStates = new Map();

const SELECTORS = {
  SEND_BUTTON: '.drive-send-btn',
  FILE_ROW: '[data-id]',
  STRONG_FILENAME: 'strong',
  INSERTION_TARGET: 'td:last-child'
};

const BUTTON_STATES = {
  NORMAL: { state: 'normal', text: 'Send', disabled: false, class: '' },
  LOADING: { state: 'loading', text: 'Sending', disabled: true, class: 'loading' },
  SUCCESS: { state: 'success', text: 'Sent', disabled: true, class: 'success' },
  ERROR: { state: 'error', text: 'Retry', disabled: false, class: 'error' }
};

const TIMEOUTS = {
  SUCCESS_RESET: 3000,
  ERROR_RESET: 5000,
  MAINTENANCE_CHECK: 2000
};

const MACHINE_READABLE_EXTENSIONS = [
  'nc', 'txt', 'gcode', 'tap', 'cnc', 'prg', 'mpf', 'iso',
  'eia', 'min', 'out', 'ngc', 'gc', 'mcd', 'mcx'
];

// Handle file interactions
function handleFileInteraction(e) {
  const fileRow = e.target.closest(SELECTORS.FILE_ROW);
  if (fileRow) {
    lastClickedFile = fileRow;
    if (!fileRow.querySelector(SELECTORS.SEND_BUTTON)) {
      addSendButton(fileRow);
    }
  }
}

// Listen for file clicks and right-clicks
document.addEventListener('click', handleFileInteraction);
document.addEventListener('contextmenu', handleFileInteraction);

// Maintain buttons when DOM changes
function maintainButton() {
  if (lastClickedFile && document.contains(lastClickedFile)) {
    if (!lastClickedFile.querySelector(SELECTORS.SEND_BUTTON)) {
      addSendButton(lastClickedFile);
    }
  }
}

// Watch for DOM changes and maintain buttons
const observer = new MutationObserver(maintainButton);
observer.observe(document.body, { childList: true, subtree: true });
setInterval(maintainButton, TIMEOUTS.MAINTENANCE_CHECK);

// Utility functions
function getFileId(fileRow) {
  return fileRow?.getAttribute('data-id');
}

function extractFileName(fileRow) {
  const strongElement = fileRow.querySelector(SELECTORS.STRONG_FILENAME);
  const name = strongElement?.textContent?.trim();
  return (name && name.includes('.')) ? name : '';
}

function hasMachineReadableExtension(fileRow) {
  const fileName = extractFileName(fileRow);
  const extension = fileName.split('.').pop()?.toLowerCase();
  return extension && MACHINE_READABLE_EXTENSIONS.includes(extension);
}

// Create and add Send button to file row
function addSendButton(fileRow) {
  if (fileRow.querySelector(SELECTORS.SEND_BUTTON) || !hasMachineReadableExtension(fileRow)) {
    return;
  }

  const fileId = getFileId(fileRow);
  const button = document.createElement('button');

  Object.assign(button.style, {
    position: 'relative',
    zIndex: '1000'
  });

  button.className = 'drive-send-btn';
  button.onclick = (e) => {
    e.stopPropagation();
    e.preventDefault();
    sendFile(fileRow);
  };

  // Apply saved or default state
  const savedStateKey = buttonStates.get(fileId) || 'NORMAL';
  setButtonState(button, fileId, BUTTON_STATES[savedStateKey]);

  const target = fileRow.querySelector(SELECTORS.INSERTION_TARGET);
  target?.appendChild(button);
}

// Send file to server
async function sendFile(fileRow) {
  const button = fileRow.querySelector(SELECTORS.SEND_BUTTON);
  if (!button) return;

  const fileId = getFileId(fileRow);
  setButtonState(button, fileId, BUTTON_STATES.LOADING);

  try {
    const settings = await chrome.storage.sync.get(['host', 'port']);
    const { host = 'test.local', port = '3000' } = settings;
    const fileName = extractFileName(fileRow) || 'file';

    chrome.runtime.sendMessage({
      action: 'downloadAndUpload',
      fileId,
      fileName,
      host,
      port
    }, (response) => {
      const newState = response?.success ? BUTTON_STATES.SUCCESS : BUTTON_STATES.ERROR;
      const resetDelay = response?.success ? TIMEOUTS.SUCCESS_RESET : TIMEOUTS.ERROR_RESET;

      setButtonState(button, fileId, newState);
      setTimeout(() => setButtonState(button, fileId, BUTTON_STATES.NORMAL), resetDelay);
    });
  } catch (error) {
    setButtonState(button, fileId, BUTTON_STATES.ERROR);
    setTimeout(() => setButtonState(button, fileId, BUTTON_STATES.NORMAL), TIMEOUTS.ERROR_RESET);
  }
}

// Set button state and appearance (unified state management)
function setButtonState(button, fileId, state) {
  if (!button || !state) return;

  // Clear all state classes
  Object.values(BUTTON_STATES).forEach(s => {
    if (s.class) button.classList.remove(s.class);
  });

  // Apply new state
  if (state.class) button.classList.add(state.class);
  button.textContent = state.text;
  button.disabled = state.disabled;

  // Store state key for persistence across DOM changes
  if (fileId) {
    // Find the key for this state object
    const stateKey = Object.keys(BUTTON_STATES).find(key => BUTTON_STATES[key] === state);
    if (stateKey) {
      buttonStates.set(fileId, stateKey);

      // Prevent memory leaks by limiting stored states
      if (buttonStates.size > 100) {
        const firstKey = buttonStates.keys().next().value;
        buttonStates.delete(firstKey);
      }
    }
  }
}

// Handle context menu messages
chrome.runtime.onMessage.addListener((request) => {
  if (request.action === 'sendFromContext') {
    const selectedRow = document.querySelector('[data-id]');
    if (selectedRow) sendFile(selectedRow);
  }
});
