/**
 * BACKGROUND SCRIPT - Core Extension Logic
 *
 * Handles extension initialization, context menu creation, and file transfer operations.
 * Runs in the background and can make cross-origin requests that content scripts cannot.
 * This is the key component that bypasses CORS restrictions for Google Drive downloads.
 *
 * Features:
 * - Creates right-click context menu for Google Drive
 * - Downloads files from Google Drive using official URLs
 * - Uploads files to user's configured server
 * - Provides async communication with content script
 */

/**
 * EXTENSION INITIALIZATION
 * Sets up the right-click context menu when extension is installed/enabled.
 * Menu only appears on Google Drive pages for relevant context.
 * Also handles initial authentication setup.
 */
chrome.runtime.onInstalled.addListener(async () => {
  // Create context menu
  chrome.contextMenus.create({
    id: "sendToDriveServer",
    title: "Send to Server",
    contexts: ["all"],                                    // Available on any page element
    documentUrlPatterns: ["*://drive.google.com/*"]      // Only show on Google Drive
  });

  // Optional: Prompt for initial authentication on install
  // This can also be done on first use instead
  try {
    await getAuthToken();
    console.log('Google Drive access granted during installation');
  } catch (error) {
    console.log('Authentication will be requested on first use:', error.message);
  }
});

/**
 * CONTEXT MENU CLICK HANDLER
 * Processes right-click menu selections and notifies the content script.
 * Content script will handle finding the relevant file and initiating transfer.
 */
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "sendToDriveServer") {
    chrome.tabs.sendMessage(tab.id, { action: "sendFromContext" });
  }
});

/**
 * OAUTH2 AUTHENTICATION
 * Gets an access token for Google Drive API access.
 * Prompts user for permission on first use.
 */
async function getAuthToken() {
  return new Promise((resolve, reject) => {
    chrome.identity.getAuthToken({ interactive: true }, (token) => {
      if (chrome.runtime.lastError) {
        reject(chrome.runtime.lastError);
      } else {
        resolve(token);
      }
    });
  });
}

/**
 * UPLOAD TO SERVER HELPER
 * Separated upload logic for reuse between different download methods.
 */
async function uploadToServer(fileBlob, fileName, host, port) {
  const formData = new FormData();
  formData.append('file', fileBlob, fileName);

  const uploadResponse = await fetch(`http://${host}:${port}/upload`, {
    method: 'POST',
    body: formData
  });

  if (uploadResponse.ok) {
    return { success: true };
  } else {
    const errorText = await uploadResponse.text().catch(() => 'Unknown error');
    throw new Error(`Upload failed (${uploadResponse.status}): ${errorText}`);
  }
}

/**
 * MESSAGE HANDLER - Content Script Communication
 * Listens for download/upload requests from content script.
 * Background script can bypass CORS restrictions that block content scripts.
 * Handles async operations and returns results to content script.
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'downloadAndUpload') {
    downloadAndUpload(request.fileId, request.fileName, request.host, request.port)
      .then(result => sendResponse(result))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Keep message channel open for async response
  }
});

/**
 * FILE DOWNLOAD AND UPLOAD PROCESSOR
 * Core function that handles the complete file transfer workflow:
 * 1. Downloads file from Google Drive using official export URL
 * 2. Converts response to blob for file handling
 * 3. Creates form data for multipart upload
 * 4. Uploads file to user's configured server
 *
 * This function runs in background script context which bypasses CORS restrictions
 * that would block the same operations in a content script.
 *
 * @param {string} fileId - Google Drive file ID extracted from DOM
 * @param {string} fileName - Human-readable file name for server
 * @param {string} host - Target server hostname
 * @param {string} port - Target server port
 * @returns {Object} Success/failure result with error details
 */
async function downloadAndUpload(fileId, fileName, host, port) {
  try {
    // STEP 1: Get OAuth token
    const token = await getAuthToken();

    // STEP 2: Get file metadata from Drive API to get the real filename
    const metadataResponse = await fetch(`https://www.googleapis.com/drive/v3/files/${fileId}?fields=name,mimeType`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!metadataResponse.ok) {
      throw new Error(`Could not get file metadata: ${metadataResponse.status} ${metadataResponse.statusText}`);
    }

    const metadata = await metadataResponse.json();
    const actualFileName = metadata.name || fileName; // Use API filename, fallback to DOM-extracted name
    const mimeType = metadata.mimeType;

    // STEP 3: Download file content from Google Drive API
    let response;

    // Check if it's a Google Workspace document that needs export
    if (mimeType.startsWith('application/vnd.google-apps.')) {
      // Export Google Docs/Sheets/Slides as plain text
      response = await fetch(`https://www.googleapis.com/drive/v3/files/${fileId}/export?mimeType=text/plain`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
    } else {
      // Direct download for regular files
      response = await fetch(`https://www.googleapis.com/drive/v3/files/${fileId}?alt=media`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
    }

    if (!response.ok) {
      throw new Error(`Could not download from Google Drive: ${response.status} ${response.statusText}`);
    }

    // STEP 4: Convert to file blob and upload with the correct filename
    const fileBlob = await response.blob();
    return await uploadToServer(fileBlob, actualFileName, host, port);

  } catch (error) {
    return { success: false, error: error.message };
  }
}
