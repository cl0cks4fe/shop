// Background script for handling file downloads and machine communication
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'sendFile') {
    handleFileSend(message.fileId, message.fileName);
  } else if (message.action === 'getSettings') {
    getSettings().then(sendResponse);
    return true; // Keep message channel open for async response
  }
});

async function handleFileSend(fileId, fileName) {
  try {
    // Get machine settings from storage
    const settings = await getSettings();
    const machineIP = settings.machineIP || '192.168.1.100';
    const machinePort = settings.machinePort || '8080';
    const uploadPath = settings.uploadPath || '/upload';

    console.log(`Sending ${fileName} to ${machineIP}:${machinePort}${uploadPath}`);

    // Download file from Google Drive
    const downloadUrl = `https://drive.google.com/uc?export=download&id=${fileId}`;

    const response = await fetch(downloadUrl);
    if (!response.ok) {
      throw new Error(`Download failed: ${response.status} ${response.statusText}`);
    }

    const fileBlob = await response.blob();

    // Send to machine gadget
    const formData = new FormData();
    formData.append('file', fileBlob, fileName);

    const uploadResponse = await fetch(`http://${machineIP}:${machinePort}${uploadPath}`, {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'VF2Controller'
      }
    });

    if (uploadResponse.ok) {
      const result = await uploadResponse.text();
      showNotification('Success', `Successfully sent ${fileName} to VF2 machine`, 'success');
      console.log('Upload successful:', result);
    } else {
      throw new Error(`Upload failed: ${uploadResponse.status} ${uploadResponse.statusText}`);
    }

  } catch (error) {
    console.error('File send error:', error);
    showNotification('Error', `Failed to send ${fileName}: ${error.message}`, 'error');
  }
}

async function getSettings() {
  const result = await browser.storage.sync.get(['machineIP', 'machinePort', 'uploadPath', 'autoDetect']);
  return {
    machineIP: result.machineIP || '192.168.1.100',
    machinePort: result.machinePort || '8080',
    uploadPath: result.uploadPath || '/upload',
    autoDetect: result.autoDetect || false
  };
}

function showNotification(title, message, type) {
  const iconUrl = type === 'success' ? 'icons/icon-48.png' : 'icons/icon-48.png';

  browser.notifications.create({
    type: 'basic',
    iconUrl: iconUrl,
    title: `VF2 Controller - ${title}`,
    message: message
  });
}
