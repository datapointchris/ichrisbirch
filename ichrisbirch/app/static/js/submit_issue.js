function openSubmitIssueWindow() {
    const window = document.getElementById('submit-issue-window');
    window.classList.add('visible');

    const overlay = document.getElementById('submit-issue-background-overlay');
    overlay.classList.add('visible');
}

function closeSubmitIssueWindow() {
    const window = document.getElementById('submit-issue-window');
    window.classList.add('box-explode');
    window.addEventListener('animationend', function hideWindow() {
        window.classList.remove('visible');
        window.classList.remove('box-explode');
        window.removeEventListener('animationend', hideWindow);
    });


    const overlay = document.getElementById('submit-issue-background-overlay');
    overlay.classList.add('fade-out');
    overlay.addEventListener('animationend', function hideOverlay() {
        overlay.classList.remove('visible');
        overlay.classList.remove('fade-out');
        overlay.removeEventListener('animationend', hideOverlay);
    });

}
