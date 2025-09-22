/**
 * CONTENT SCRIPT - Google Drive Page Integration
 *
 * Runs on Google Drive pages to add "Send" buttons to files.
 * Handles user interactions and coordinates with background script for file transfers.
 *
 * Features:
 * - Detects file clicks/right-clicks and adds Send buttons
 * - Maintains buttons even when Google Drive updates the DOM
 * - Extracts file information (ID, name) from Google Drive DOM
 * - Communicates with background script to handle actual file transfer
 * - Provides user feedback via alerts
 */

let lastClickedFile = null;

/**
 * BUTTON STATE TRACKING
 * Maps file IDs to their current button states to preserve state across DOM changes
 */
const buttonStates = new Map();

/**
 * CONSTANTS
 */
const SELECTORS = {
  SEND_BUTTON: '.drive-send-btn',
  FILE_ROW: '[data-id]',
  STRONG_FILENAME: 'strong.DNoYtb',
  INSERTION_TARGETS: [
    '[role="gridcell"]:last-child',
  ]
};

const BUTTON_STATES = {
  NORMAL: 'normal',
  LOADING: 'loading',
  SUCCESS: 'success',
  ERROR: 'error'
};

const TIMEOUTS = {
  SUCCESS_RESET: 3000,
  ERROR_RESET: 5000,
  MAINTENANCE_CHECK: 2000,
  STATUS_CLEAR: 2000
};

/**
 * MACHINE-READABLE FILE EXTENSIONS
 * Array of file extensions that should show the Send button.
 * Only files with these extensions will have the Send functionality.
 */
const MACHINE_READABLE_EXTENSIONS = [
  'nc',     // CNC G-code files
  'txt',    // Text files
  'gcode',  // G-code files
  'tap',    // CNC tap files
  'cnc',    // CNC files
  'prg',    // Program files
  'mpf',    // Machine program files
  'iso',    // ISO G-code files
  'eia',    // EIA G-code files
  'min',    // Minimal G-code files
  'out',    // Output files
  'ngc',    // LinuxCNC files
  'gc',     // G-code files
  'mcd',    // Mastercam files
  'mcx'     // Mastercam exchange files
];

/**
 * FILE INTERACTION HANDLER
 * Handles file clicks and right-clicks to add Send buttons.
 * Consolidated logic to avoid duplication.
 */
function handleFileInteraction(e) {
  const fileRow = e.target.closest(SELECTORS.FILE_ROW);
  if (fileRow) {
    lastClickedFile = fileRow;
    if (!fileRow.querySelector(SELECTORS.SEND_BUTTON)) {
      addSendButton(fileRow);
    }
  }
}

/**
 * FILE CLICK AND CONTEXT MENU DETECTION
 * Listens for both clicks and right-clicks on files.
 */
document.addEventListener('click', handleFileInteraction);
document.addEventListener('contextmenu', handleFileInteraction);

/**
 * BUTTON MAINTENANCE
 * Re-adds send button to last clicked file if it gets removed by Drive's DOM updates.
 */
function maintainButton() {
  if (lastClickedFile && document.contains(lastClickedFile)) {
    if (!lastClickedFile.querySelector(SELECTORS.SEND_BUTTON)) {
      addSendButton(lastClickedFile);
    }
  }
}

/**
 * DOM MUTATION OBSERVER
 * Watches for Google Drive DOM changes and maintains buttons.
 */
const observer = new MutationObserver(maintainButton);
observer.observe(document.body, { childList: true, subtree: true });

/**
 * PERIODIC BUTTON MAINTENANCE
 * Backup maintenance check every 2 seconds.
 */
setInterval(maintainButton, TIMEOUTS.MAINTENANCE_CHECK);

/**
 * FILENAME EXTRACTION UTILITY
 * Centralized function to extract filename from Google Drive DOM elements.
 * Uses multiple fallback strategies to find the filename reliably.
 *
 * @param {Element} fileRow - The DOM element representing a file in Google Drive
 * @returns {string} - The extracted filename or empty string if not found
 */
function extractFileName(fileRow) {
  // Try to get the clean filename from the strong tag first
  const strongElement = fileRow.querySelector('strong.DNoYtb');
  if (strongElement) {
    const name = strongElement.textContent?.trim();
    if (name && name.includes('.')) {
      return name;
    }
  }

  // Fallback selectors if strong tag doesn't work
  const selectors = [
    '[title]',
    'span[role="button"]',
    '[aria-label*="."]',
    'div[data-target]'
  ];

  for (const selector of selectors) {
    const element = fileRow.querySelector(selector);
    if (element) {
      let name = element.getAttribute('title') ||
                 element.getAttribute('aria-label') ||
                 element.textContent?.trim();

      if (name && name.length > 0 && name !== 'More actions' && name.includes('.')) {
        // Clean up filename - remove extra text after the extension
        const match = name.match(/^(.+\.[a-zA-Z0-9]+)/);
        if (match) {
          return match[1].trim();
        } else {
          return name.trim();
        }
      }
    }
  }

  return ''; // No filename found
}

/**
 * MACHINE-READABLE EXTENSION CHECK
 * Checks if a file has an extension that qualifies for machine transfer.
 *
 * @param {Element} fileRow - The DOM element representing a file in Google Drive
 * @returns {boolean} - True if file has machine-readable extension
 */
function hasMachineReadableExtension(fileRow) {
  const fileName = extractFileName(fileRow);
  if (!fileName) return false;

  const lastDotIndex = fileName.lastIndexOf('.');
  if (lastDotIndex === -1) return false;

  const extension = fileName.substring(lastDotIndex + 1).toLowerCase();
  return MACHINE_READABLE_EXTENSIONS.includes(extension);
}

/**
 * SEND BUTTON CREATION
 * Creates and adds a "Send" button to a specific file row.
 * Button is styled via CSS and prevents event bubbling to avoid interfering with Drive UI.
 * Uses multiple strategies to find the best insertion point.
 * Only adds button if file has a machine-readable extension.
 *
 * @param {Element} fileRow - The DOM element representing a file in Google Drive
 */
function addSendButton(fileRow) {
  // Don't add if button already exists
  if (fileRow.querySelector('.drive-send-btn')) return;

  // Check if file has machine-readable extension
  if (!hasMachineReadableExtension(fileRow)) return;

  const fileId = fileRow.getAttribute('data-id');
  const button = document.createElement('button');
  button.className = 'drive-send-btn';
  button.style.position = 'relative';
  button.style.zIndex = '1000';
  button.onclick = (e) => {
    e.stopPropagation();  // Prevent triggering Drive's file selection
    e.preventDefault();
    sendFile(fileRow);
  };

  // Restore previous button state if it exists, otherwise set to normal
  const savedState = buttonStates.get(fileId) || { state: 'normal', text: 'Send' };
  restoreButtonState(button, savedState);

  // Try different insertion strategies
  const insertionTargets = [
    fileRow.querySelector('[role="gridcell"]:last-child'),
    fileRow.querySelector('.Q5txwe'),
    fileRow.lastElementChild,
    fileRow
  ];

  for (const target of insertionTargets) {
    if (target) {
      try {
        target.appendChild(button);
        break;
      } catch (e) {
        continue;
      }
    }
  }

  // Mark the row as having our button
  fileRow.setAttribute('data-has-send-btn', 'true');
}

/**
 * FILE TRANSFER INITIATION
 * Extracts file information from Google Drive DOM and sends transfer request to background script.
 * The background script handles the actual download/upload to avoid CORS issues.
 * Provides visual feedback through button state changes.
 *
 * @param {Element} fileRow - The DOM element containing file information
 */
async function sendFile(fileRow) {
  const button = fileRow.querySelector('.drive-send-btn');
  if (!button) return;

  // Set loading state
  setButtonState(button, 'loading');

  // Get user's server configuration
  const settings = await chrome.storage.sync.get(['host', 'port']);
  const host = settings.host || 'test.local';
  const port = settings.port || '3000';

  // Extract file information from Google Drive DOM
  const fileId = fileRow.getAttribute('data-id');
  const fileName = extractFileName(fileRow) || 'file';

  // Send transfer request to background script (which can bypass CORS)
  chrome.runtime.sendMessage({
    action: 'downloadAndUpload',
    fileId: fileId,
    fileName: fileName,
    host: host,
    port: port
  }, (response) => {
    // Update button state - works even if button was removed/re-created
    if (response.success) {
      updateButtonStateById(fileId, BUTTON_STATES.SUCCESS);
      setTimeout(() => updateButtonStateById(fileId, BUTTON_STATES.NORMAL), TIMEOUTS.SUCCESS_RESET);
    } else {
      updateButtonStateById(fileId, BUTTON_STATES.ERROR);
      setTimeout(() => updateButtonStateById(fileId, BUTTON_STATES.NORMAL), TIMEOUTS.ERROR_RESET);
    }
  });
}

/**
 * UPDATE BUTTON STATE BY FILE ID
 * Updates button state for a specific file, whether the button currently exists or not.
 * Always updates the saved state, and updates the DOM button if it exists.
 *
 * @param {string} fileId - The Google Drive file ID
 * @param {string} state - 'normal', 'loading', 'success', or 'error'
 */
function updateButtonStateById(fileId, state) {
  // First, find the button in the DOM if it exists
  const fileRow = document.querySelector(`[data-id="${fileId}"]`);
  const button = fileRow?.querySelector('.drive-send-btn');

  if (button) {
    // Button exists, update it normally
    setButtonState(button, state);
  } else {
    // Button doesn't exist, just update the saved state
    let buttonInfo = { state: state };

    switch (state) {
      case 'loading':
        buttonInfo.text = 'Sending';
        break;
      case 'success':
        buttonInfo.text = 'Sent';
        break;
      case 'error':
        buttonInfo.text = 'Retry';
        break;
      case 'normal':
      default:
        buttonInfo.text = 'Send';
        buttonInfo.state = 'normal';
        break;
    }

    // Save state for when button gets re-created
    buttonStates.set(fileId, buttonInfo);

    // Clean up old states when map gets too large
    if (buttonStates.size > 100) {
      const firstKey = buttonStates.keys().next().value;
      buttonStates.delete(firstKey);
    }
  }
}

/**
 * BUTTON STATE MANAGEMENT
 * Updates button appearance and behavior based on upload state.
 * Also saves the state so it can be restored if button gets re-created.
 *
 * @param {Element} button - The send button element
 * @param {string} state - 'normal', 'loading', 'success', or 'error'
 */
function setButtonState(button, state) {
  const fileRow = button.closest('[data-id]');
  const fileId = fileRow?.getAttribute('data-id');

  // Reset all state classes
  button.classList.remove('loading', 'success', 'error');

  let buttonInfo = { state: state };

  switch (state) {
    case 'loading':
      button.classList.add('loading');
      button.textContent = 'Sending';
      button.disabled = true;
      buttonInfo.text = 'Sending';
      break;

    case 'success':
      button.classList.add('success');
      button.textContent = 'Sent';
      button.disabled = true;
      buttonInfo.text = 'Sent';
      break;

    case 'error':
      button.classList.add('error');
      button.textContent = 'Retry';
      button.disabled = false;
      buttonInfo.text = 'Retry';
      break;

    case 'normal':
    default:
      button.textContent = 'Send';
      button.disabled = false;
      buttonInfo.text = 'Send';
      buttonInfo.state = 'normal';
      break;
  }

  // Save button state for restoration
  if (fileId) {
    buttonStates.set(fileId, buttonInfo);

    // Clean up old states when map gets too large (prevent memory leak)
    if (buttonStates.size > 100) {
      const firstKey = buttonStates.keys().next().value;
      buttonStates.delete(firstKey);
    }
  }
}

/**
 * BUTTON STATE RESTORATION
 * Restores a button to its previously saved state.
 *
 * @param {Element} button - The send button element
 * @param {Object} savedState - Previously saved button state
 */
function restoreButtonState(button, savedState) {
  button.classList.remove('loading', 'success', 'error');

  switch (savedState.state) {
    case 'loading':
      button.classList.add('loading');
      button.textContent = savedState.text;
      button.disabled = true;
      break;

    case 'success':
      button.classList.add('success');
      button.textContent = savedState.text;
      button.disabled = true;
      break;

    case 'error':
      button.classList.add('error');
      button.textContent = savedState.text;
      button.disabled = false;
      break;

    case 'normal':
    default:
      button.textContent = savedState.text;
      button.disabled = false;
      break;
  }
}

/**
 * CONTEXT MENU HANDLER
 * Handles messages from the background script when user uses right-click context menu.
 * Finds the first available file and attempts to send it.
 */
chrome.runtime.onMessage.addListener((request) => {
  if (request.action === 'sendFromContext') {
    const selectedRow = document.querySelector('[data-id]');
    if (selectedRow) sendFile(selectedRow);
  }
});
