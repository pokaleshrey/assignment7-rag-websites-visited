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
          func: (highlight_text) => {
            const findAndHighlightText = (text) => {
              const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
                acceptNode: (node) => node.textContent.includes(text) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT
              });

              const textNode = walker.nextNode();

              if (textNode) {
                const range = document.createRange();
                const startIndex = textNode.textContent.indexOf(text);
                const endIndex = startIndex + text.length;
                range.setStart(textNode, startIndex);
                range.setEnd(textNode, endIndex);

                const rect = range.getBoundingClientRect();
                const highlightDiv = document.createElement('div');
                highlightDiv.style.position = 'absolute';
                highlightDiv.style.left = `${rect.left + window.scrollX}px`;
                highlightDiv.style.top = `${rect.top + window.scrollY}px`;
                highlightDiv.style.width = `${rect.width}px`;
                highlightDiv.style.height = `${rect.height}px`;
                highlightDiv.style.border = '2px solid red';
                highlightDiv.style.zIndex = '9999';
                document.body.appendChild(highlightDiv);

                window.scrollTo({ top: rect.top + window.scrollY - 100, behavior: 'smooth' });
              }
            };

            findAndHighlightText(highlight_text);
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