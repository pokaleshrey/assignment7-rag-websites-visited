// Utility function for structured debug messages
function logDebug(message, data = null) {
  if (data) {
    console.debug(`[DEBUG] ${message}`, data);
  } else {
    console.debug(`[DEBUG] ${message}`);
  }
}

// Add a cache to track processed tab IDs and URLs
const processedTabs = new Map();

chrome.webNavigation.onCompleted.addListener(async (details) => {
  try {
    logDebug('In method');

    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (tab && tab.id === details.tabId) {
      // Check if this tab and URL have already been processed
      const cachedUrl = processedTabs.get(tab.id);
      if (cachedUrl === details.url) {
        logDebug('Duplicate event detected, skipping processing', { tabId: tab.id, url: details.url });
        return;
      }

      const tabContent = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => ({
          url: window.location.href,
          body: document.documentElement.outerHTML
        })
      });

      if (tabContent && tabContent[0] && tabContent[0].result) {
        const { url, body } = tabContent[0].result;

        logDebug('URL and HTML extracted', { url, body });

        const requestOptions = {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': chrome.runtime.getURL('')
          },
          body: JSON.stringify({ url, body }),
          mode: 'cors'
        };

        await fetch('http://127.0.0.1:8080/index-website', requestOptions)
          .then(response => {
            if (!response.ok) {
              if (response.status === 404) {
                throw new Error('Stock price service not found. Is the server running?');
              } else if (response.status === 403) {
                throw new Error('Access to stock price service is forbidden. Check CORS settings.');
              }
              throw new Error(`HTTP error! status: ${response.status}`);
            }

            return response.json();
          })
          .then(data => {
            logDebug('API Response data', data);
            // Update the cache with the processed URL
            processedTabs.set(tab.id, details.url);
          })
          .catch(error => {
            console.error('Error calling web service:', error);
            let errorMessage = 'Failed to connect to stock price service:\n';
            if (chrome.notifications && chrome.notifications.create) {
              chrome.notifications.create({
                type: 'basic',
                iconUrl: 'icon.png', // Replace with the path to your extension's icon
                title: 'Error',
                message: errorMessage + error.message
              });
            } else {
              logDebug('Notifications API is not available in this context.');
            }
          });
      }
    }
  } catch (error) {
    console.error('Error sending webpage data:', error);
  }
});
