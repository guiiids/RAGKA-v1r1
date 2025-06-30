// JavaScript to call /api/query, get Markdown string, render with marked.js, and insert into chat-messages container

document.addEventListener('DOMContentLoaded', () => {
  const chatMessagesContainer = document.getElementById('chat-messages');
  const queryInput = document.getElementById('query-input');
  const submitBtn = document.getElementById('submit-btn');

  async function fetchAndRenderMarkdown(query) {
    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: query })
      });
      const data = await response.json();
      if (data.error) {
        chatMessagesContainer.innerHTML += `<div class="bot-message"><div class="bot-bubble">Error: ${data.error}</div></div>`;
        return;
      }
      const markdown = data.answer || '';
      const html = marked.parse(markdown);
      chatMessagesContainer.innerHTML += `<div class="bot-message"><div class="bot-bubble">${html}</div></div>`;
      chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    } catch (error) {
      chatMessagesContainer.innerHTML += `<div class="bot-message"><div class="bot-bubble">Error fetching response</div></div>`;
    }
  }

  submitBtn.addEventListener('click', () => {
    const query = queryInput.value.trim();
    if (!query) return;
    // Show user message
    chatMessagesContainer.innerHTML += `<div class="user-message"><div class="user-bubble">${query}</div></div>`;
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    queryInput.value = '';
    fetchAndRenderMarkdown(query);
  });

  // Optional: submit on Enter key
  queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitBtn.click();
    }
  });
});