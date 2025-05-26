let hasSubmitted = false;
//Example of a function to render a message with thumbs up/down feedback
// This function would be called when a message is received
// from the AI
function renderMessage(text) {
  hasSubmitted = false; // Reset flag
  const container = document.getElementById('chat-container');
  container.innerHTML = `
    <div class="message">${text}</div>
    <div class="feedback-header" style="display:flex; justify-content:space-between; align-items:center; margin-top:8px; font-size:16px;">
      <span>Was this helpful?</span>
      <div style="font-size:24px; cursor:pointer;">
        <span id="thumbs-up">👍</span>
        <span id="thumbs-down" style="margin-left:10px;">👎</span>
      </div>
    </div>
    <div id="feedback-area" style="margin-top:10px;"></div>
  `;

  document.getElementById('thumbs-up').onclick = () => {}; // Placeholder for thumbs-up logic
  document.getElementById('thumbs-down').onclick = () => {
    if (!hasSubmitted) loadDownReasons();
  };
}

function loadDownReasons() {
  const reasons = [
    "Factual Error / Inaccurate",
    "Data Source Quality / Missing",
    "Missing Information / Incomplete",
    "Irrelevant / Didn't Answer Question",
    "Unclear / Confusing Language",
    "Other Issue"
  ];

  const checkboxes = reasons.map(reason =>
    `<label><input type="checkbox" class="reason" value="${reason}"> ${reason}</label><br>`
  ).join('');

  const feedbackArea = document.getElementById('feedback-area');
  feedbackArea.innerHTML = `
    <form id="feedback-form" role="form" aria-labelledby="feedback-header">
      <fieldset>
        <legend id="feedback-header">Select the issues:</legend>
        <div id="reason-box">${checkboxes}</div>
      </fieldset>
      <div id="comment-box" style="margin-top:10px; display:none;">
        <label for="comment">Help us to improve the chat bot and tell us what happened:</label>
        <textarea id="comment" aria-label="Additional comments" placeholder="Help us to improve the chat bot and tell us what happened:" style="width:100%; height:60px;"></textarea>
      </div>
      <button type="button" id="submit-btn" style="margin-top:5px;">Submit</button>
    </form>
  `;

  document.querySelectorAll('.reason').forEach(cb => {
    cb.onchange = () => {
      const anyChecked = [...document.querySelectorAll('.reason')].some(c => c.checked);
      document.getElementById('comment-box').style.display = anyChecked ? 'block' : 'none';
    };
  });

  document.getElementById('submit-btn').onclick = submitFeedback;
}

function submitFeedback() {
  if (hasSubmitted) return;

  const selected = [...document.querySelectorAll('.reason')].filter(c => c.checked);
  if (selected.length === 0) {
    alert("Please select at least one reason.");
    return;
  }

  hasSubmitted = true;
  const reasons = selected.map(c => c.value);
  const comment = document.getElementById('comment').value;

  // Simulated backend call here
  console.log("Submitted thumbs down with:", reasons, comment);

  document.getElementById('feedback-area').innerHTML = `<div style="color:green; font-weight:bold;">Thank you for sharing your feedback.</div>`;
}

// Example usage:
renderMessage("This is your AI-generated response.");
