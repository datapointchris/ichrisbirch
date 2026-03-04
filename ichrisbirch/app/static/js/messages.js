function closeFlashMessage(button) {
    const message = button.parentNode;
    message.style.opacity = 0;
    setTimeout(() => {
      message.parentNode.removeChild(message);
    }, 1000);
  }

  function showFlashMessage(message, category) {
    let container = document.querySelector('.flash-messages');
    if (!container) {
      container = document.createElement('div');
      container.className = 'flash-messages';
      const header = document.querySelector('header');
      header.parentNode.insertBefore(container, header.nextSibling);
    }
    const div = document.createElement('div');
    div.className = 'flash-messages__message flash-messages__message--' + category;
    div.textContent = message;
    const btn = document.createElement('button');
    btn.className = 'flash-messages__close-button';
    btn.textContent = 'X';
    btn.onclick = function() { closeFlashMessage(this); };
    div.appendChild(btn);
    container.appendChild(div);
  }

  const messages = document.getElementById('flash-messages');
  if (messages) {
    const closeButtons = messages.querySelectorAll('.close-button');
    closeButtons.forEach((button) => {
      button.addEventListener('click', () => {
        closeFlashMessage(button);
      });
    });
  }
