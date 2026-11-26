const form = document.getElementById('chat-form');
if (form) {
  const input = document.getElementById('message-input');
  const messages = document.getElementById('messages');
  function addMessage(text, who) {
    const bubble = document.createElement('div');
    bubble.className = `message ${who}`;
    bubble.textContent = text;
    messages.appendChild(bubble);
    messages.scrollTop = messages.scrollHeight;
    return bubble;
  }
  async function sendMessage(text) {
    if (!text.trim()) return;
    document.querySelector('.suggestions')?.remove();
    addMessage(text, 'user');
    input.value = '';
    input.disabled = true;
    const waiting = addMessage('Thinking…', 'bot');
    try {
      const response = await fetch('/api/chat', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: text})
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.reply || 'Unable to process your message.');
      }
      waiting.textContent = data.reply || 'Sorry, something went wrong.';
    } catch (_error) {
      waiting.textContent = 'Unable to connect right now. Please try again.';
    } finally {
      input.disabled = false;
      input.focus();
      messages.scrollTop = messages.scrollHeight;
    }
  }
  form.addEventListener('submit', event => { event.preventDefault(); sendMessage(input.value); });
  document.querySelectorAll('[data-message]').forEach(button => button.addEventListener('click', () => sendMessage(button.dataset.message)));
}
