#!/bin/bash
mkdir -p gadget-extension-temp/{chrome,firefox}
cp extension/* gadget-extension-temp/chrome/ 2>/dev/null || true
cp extension/* gadget-extension-temp/firefox/ 2>/dev/null || true
cp extension/manifests/manifest-chrome.json gadget-extension-temp/chrome/manifest.json
cp extension/manifests/manifest-firefox.json gadget-extension-temp/firefox/manifest.json
