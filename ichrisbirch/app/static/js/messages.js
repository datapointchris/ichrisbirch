function closeFlashMessage(button) {
    const message = button.parentNode;
    message.style.opacity = 0;
    setTimeout(() => {
      message.parentNode.removeChild(message);
    }, 1000);
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

