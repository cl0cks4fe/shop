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
 */
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "sendToDriveServer",
    title: "Send to Server",
    contexts: ["all"],                                    // Available on any page element
    documentUrlPatterns: ["*://drive.google.com/*"]      // Only show on Google Drive
  });
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
    // STEP 1: Download from Google Drive
    // Uses official Google Drive export URL that works with user's existing session
    const downloadUrl = `https://drive.google.com/uc?export=download&id=${fileId}`;
    const response = await fetch(downloadUrl);
    
    if (!response.ok) {
      throw new Error('Could not download from Google Drive');
    }
    
    // STEP 2: Convert to file blob
    const fileBlob = await response.blob();
    const formData = new FormData();
    formData.append('file', fileBlob, fileName);
    
    // STEP 3: Upload to user's server
    // Posts as multipart/form-data which most servers expect for file uploads
    const uploadResponse = await fetch(`http://${host}:${port}/upload`, {
      method: 'POST',
      body: formData
    });
    
    if (uploadResponse.ok) {
      return { success: true };
    } else {
      throw new Error('Upload failed');
    }
    
  } catch (error) {
    return { success: false, error: error.message };
  }
}
