/* Background Script - Extension Core Logic */

// Initialize context menu for Google Drive
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "downloadFromDrive",
    title: "Send to Server",
    contexts: ["all"],
    documentUrlPatterns: ["*://drive.google.com/*"]
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "downloadFromDrive") {
    chrome.tabs.sendMessage(tab.id, { action: "sendFromContext" });
  }
});

// Handle messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'downloadAndUpload') {
    downloadAndUpload(request.fileId, request.fileName, request.host, request.port)
      .then(result => sendResponse(result))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
});

// Download from Google Drive and upload to server
async function downloadAndUpload(fileId, fileName, host, port) {
  try {
    // Download from Google Drive
    const downloadUrl = `https://drive.google.com/uc?export=download&id=${fileId}`;
    const response = await fetch(downloadUrl);

    if (!response.ok) {
      throw new Error('Could not download from Google Drive');
    }

    // Convert to file blob and prepare upload
    const fileBlob = await response.blob();
    const formData = new FormData();
    formData.append('file', fileBlob, fileName);

    // Upload to server
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
