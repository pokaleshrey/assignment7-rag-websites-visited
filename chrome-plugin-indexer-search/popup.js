document.getElementById('searchButton').addEventListener('click', () => {
  const searchText = document.getElementById('searchInput').value;

  if (searchText.trim() === '') {
    alert('Please enter text to search.');
    return;
  }

  fetch('http://127.0.0.1:8081/search-agent', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query: searchText })
  })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      const { url, highlight_text } = data;

      chrome.tabs.create({ url }, (tab) => {
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: (highlightText) => {
            const range = document.createRange();
            const selection = window.getSelection();
            const textNode = Array.from(document.body.querySelectorAll('*'))
              .find(node => node.textContent.includes(highlightText));

            if (textNode) {
              range.selectNodeContents(textNode);
              selection.removeAllRanges();
              selection.addRange(range);
            }
          },
          args: [highlight_text]
        });
      });
    })
    .catch(error => {
      console.error('Error during search:', error);
      alert(`Error: ${error.message}`);
    });
});