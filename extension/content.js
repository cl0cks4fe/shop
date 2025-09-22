// Content script that runs on Google Drive pages to add VF2 send buttons
let isInitialized = false;

function init() {
  if (isInitialized) return;
  isInitialized = true;

  console.log('VF2 Controller: Initializing on Google Drive');

  // Wait for Google Drive to load and add buttons
  setTimeout(() => {
    addMachineButtons();
    setupObserver();
  }, 2000);
}

function addMachineButtons() {
  // Look for file items in Google Drive interface
  const fileSelectors = [
    '[data-target="file"]',
    '[data-id][jsaction*="click"]',
    '.Qr7Oae', // Grid view items
    '.a-u-Z.KL4NAf' // List view items
  ];

  let fileItems = [];
  fileSelectors.forEach(selector => {
    const elements = document.querySelectorAll(selector);
    fileItems = fileItems.concat(Array.from(elements));
  });

  console.log(`VF2 Controller: Found ${fileItems.length} potential file items`);

  fileItems.forEach(item => {
    if (item.querySelector('.vf2-send-btn')) return; // Already has button

    const fileName = getFileName(item);
    if (!fileName || !fileName.toLowerCase().includes('.nc')) return; // Only .nc files

    addSendButton(item, fileName);
  });
}

function getFileName(element) {
  // Try different methods to extract filename from Google Drive elements
  const selectors = [
    '[title]',
    '[data-tooltip]',
    '.sSzDje', // File name in list view
    '.KL4NAf .sSzDje',
    'span[title]'
  ];

  for (const selector of selectors) {
    const nameElement = element.querySelector(selector);
    if (nameElement) {
      const title = nameElement.getAttribute('title') || nameElement.textContent;
      if (title && title.trim()) {
        return title.trim();
      }
    }
  }

  return null;
}

function addSendButton(fileElement, fileName) {
  const button = document.createElement('button');
  button.className = 'vf2-send-btn';
  button.innerHTML = '📤 VF2';
  button.title = `Send ${fileName} to VF2 machine`;

  // Style the button
  button.style.cssText = `
    margin: 4px;
    padding: 4px 8px;
    background: #1976d2;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 11px;
    font-family: Google Sans, Roboto, sans-serif;
    font-weight: 500;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    transition: all 0.2s;
    z-index: 1000;
    position: relative;
  `;

  // Hover effects
  button.onmouseenter = () => {
    button.style.background = '#1565c0';
    button.style.boxShadow = '0 2px 6px rgba(0,0,0,0.3)';
  };

  button.onmouseleave = () => {
    button.style.background = '#1976d2';
    button.style.boxShadow = '0 1px 3px rgba(0,0,0,0.2)';
  };

  button.onclick = (e) => {
    e.stopPropagation();
    e.preventDefault();
    sendFileToMachine(fileElement, fileName, button);
  };

  // Find appropriate place to insert button
  const actionArea = fileElement.querySelector('[jsaction], .a-u-Z-d') || fileElement;
  actionArea.appendChild(button);

  console.log(`VF2 Controller: Added send button for ${fileName}`);
}

function sendFileToMachine(fileElement, fileName, button) {
  const fileId = extractFileId(fileElement);
  if (!fileId) {
    showStatus(button, 'Error: Could not identify file', 'error');
    return;
  }

  console.log(`VF2 Controller: Sending ${fileName} (ID: ${fileId})`);

  // Update button state
  showStatus(button, 'Sending...', 'loading');

  // Send message to background script
  browser.runtime.sendMessage({
    action: 'sendFile',
    fileId: fileId,
    fileName: fileName
  });

  // Reset button after delay
  setTimeout(() => {
    showStatus(button, '📤 VF2', 'normal');
  }, 3000);
}

function extractFileId(element) {
  // Try to extract Google Drive file ID from various attributes
  const attributes = ['data-id', 'id'];

  for (const attr of attributes) {
    const id = element.getAttribute(attr);
    if (id && id.match(/^[a-zA-Z0-9_-]{20,}/)) {
      return id;
    }
  }

  // Try to find file ID in href attributes
  const links = element.querySelectorAll('a[href*="/file/d/"]');
  for (const link of links) {
    const match = link.href.match(/\/file\/d\/([a-zA-Z0-9_-]+)/);
    if (match) {
      return match[1];
    }
  }

  // Try data attributes on child elements
  const dataElements = element.querySelectorAll('[data-id]');
  for (const el of dataElements) {
    const id = el.getAttribute('data-id');
    if (id && id.match(/^[a-zA-Z0-9_-]{20,}/)) {
      return id;
    }
  }

  console.warn('VF2 Controller: Could not extract file ID from element', element);
  return null;
}

function showStatus(button, text, type) {
  const originalText = button.innerHTML;
  button.innerHTML = text;

  switch (type) {
    case 'loading':
      button.style.background = '#ff9800';
      button.disabled = true;
      break;
    case 'success':
      button.style.background = '#4caf50';
      break;
    case 'error':
      button.style.background = '#f44336';
      break;
    case 'normal':
    default:
      button.style.background = '#1976d2';
      button.disabled = false;
      break;
  }
}

function setupObserver() {
  // Watch for dynamic content changes in Google Drive
  const observer = new MutationObserver((mutations) => {
    let shouldUpdate = false;

    mutations.forEach((mutation) => {
      if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
        shouldUpdate = true;
      }
    });

    if (shouldUpdate) {
      // Debounce updates
      clearTimeout(window.vf2UpdateTimeout);
      window.vf2UpdateTimeout = setTimeout(addMachineButtons, 1000);
    }
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true
  });

  console.log('VF2 Controller: Mutation observer setup complete');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// Also try to initialize after a delay to handle dynamic loading
setTimeout(init, 3000);
