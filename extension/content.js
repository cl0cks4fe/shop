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
 * FILE CLICK DETECTION
 * Listens for clicks anywhere on the page and checks if user clicked on a file.
 * If a file is clicked and doesn't already have a Send button, adds one.
 * Stores reference to maintain button persistence.
 */
document.addEventListener('click', (e) => {
  const fileRow = e.target.closest('[data-id]');
  if (fileRow) {
    lastClickedFile = fileRow;
    if (!fileRow.querySelector('.drive-send-btn')) {
      addSendButton(fileRow);
    }
  }
});

/**
 * FILE RIGHT-CLICK DETECTION
 * Listens for right-clicks (context menu) on files.
 * Also adds Send button when user right-clicks on a file.
 */
document.addEventListener('contextmenu', (e) => {
  const fileRow = e.target.closest('[data-id]');
  if (fileRow) {
    lastClickedFile = fileRow;
    if (!fileRow.querySelector('.drive-send-btn')) {
      addSendButton(fileRow);
    }
  }
});

/**
 * DOM MUTATION OBSERVER
 * Watches for Google Drive DOM changes and re-adds buttons when they get removed.
 * This handles the case where Drive updates the UI and removes our buttons.
 */
const observer = new MutationObserver(() => {
  // Re-add button to last clicked file if it's missing
  if (lastClickedFile && !lastClickedFile.querySelector('.drive-send-btn')) {
    // Check if the element is still in the DOM
    if (document.contains(lastClickedFile)) {
      addSendButton(lastClickedFile);
    }
  }
});

// Start observing DOM changes
observer.observe(document.body, {
  childList: true,
  subtree: true
});

/**
 * PERIODIC BUTTON MAINTENANCE
 * Checks every 2 seconds if the last clicked file still has its button.
 * Re-adds it if Google Drive removed it during DOM updates.
 */
setInterval(() => {
  if (lastClickedFile && document.contains(lastClickedFile)) {
    if (!lastClickedFile.querySelector('.drive-send-btn')) {
      addSendButton(lastClickedFile);
    }
  }
}, 2000);

/**
 * MACHINE-READABLE EXTENSION CHECK
 * Checks if a file has an extension that qualifies for machine transfer.
 * Extracts filename from Google Drive DOM and validates against allowed extensions.
 * 
 * @param {Element} fileRow - The DOM element representing a file in Google Drive
 * @returns {boolean} - True if file has machine-readable extension
 */
function hasMachineReadableExtension(fileRow) {
  // Try to get the filename from various DOM selectors
  let fileName = '';
  
  // First try to get the clean filename from the strong tag
  const strongElement = fileRow.querySelector('strong.DNoYtb');
  if (strongElement) {
    const name = strongElement.textContent?.trim();
    if (name && name.includes('.')) {
      fileName = name;
    }
  }
  
  // If not found, try fallback selectors
  if (!fileName) {
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
            fileName = match[1].trim();
          } else {
            fileName = name.trim();
          }
          break;
        }
      }
    }
  }
  
  // If no filename found, don't show button
  if (!fileName) return false;
  
  // Extract file extension
  const lastDotIndex = fileName.lastIndexOf('.');
  if (lastDotIndex === -1) return false; // No extension
  
  const extension = fileName.substring(lastDotIndex + 1).toLowerCase();
  
  // Check if extension is in our allowed list
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
  
  const button = document.createElement('button');
  button.textContent = 'Send';
  button.className = 'drive-send-btn';
  button.style.position = 'relative';
  button.style.zIndex = '1000';
  button.onclick = (e) => {
    e.stopPropagation();  // Prevent triggering Drive's file selection
    e.preventDefault();
    sendFile(fileRow);
  };
  
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
  const fileId = fileRow.getAttribute('data-id');  // Google Drive's unique file ID
  
  // Try multiple selectors to get the clean filename
  let fileName = 'file';
  
  // First try to get the clean filename from the strong tag
  const strongElement = fileRow.querySelector('strong.DNoYtb');
  if (strongElement) {
    const name = strongElement.textContent?.trim();
    if (name && name.includes('.')) {
      fileName = name;
    }
  } else {
    // Fallback to other selectors
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
            fileName = match[1].trim();
          } else {
            fileName = name.trim();
          }
          break;
        }
      }
    }
  }
  
  // Send transfer request to background script (which can bypass CORS)
  chrome.runtime.sendMessage({
    action: 'downloadAndUpload',
    fileId: fileId,
    fileName: fileName,
    host: host,
    port: port
  }, (response) => {
    // Update button based on result
    if (response.success) {
      setButtonState(button, 'success');
      // Reset to normal state after 3 seconds
      setTimeout(() => setButtonState(button, 'normal'), 3000);
    } else {
      setButtonState(button, 'error');
      // Reset to normal state after 5 seconds (allow retry)
      setTimeout(() => setButtonState(button, 'normal'), 5000);
    }
  });
}

/**
 * BUTTON STATE MANAGEMENT
 * Updates button appearance and behavior based on upload state.
 * 
 * @param {Element} button - The send button element
 * @param {string} state - 'normal', 'loading', 'success', or 'error'
 */
function setButtonState(button, state) {
  // Reset all state classes
  button.classList.remove('loading', 'success', 'error');
  
  switch (state) {
    case 'loading':
      button.classList.add('loading');
      button.textContent = 'Sending';
      button.disabled = true;
      break;
      
    case 'success':
      button.classList.add('success');
      button.textContent = 'Sent';
      button.disabled = true;
      break;
      
    case 'error':
      button.classList.add('error');
      button.textContent = 'Retry';
      button.disabled = false;
      break;
      
    case 'normal':
    default:
      button.textContent = 'Send';
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
