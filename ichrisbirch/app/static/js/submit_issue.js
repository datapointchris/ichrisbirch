function openSubmitIssueWindow() {
    const issueWindow = document.getElementById('github-issue-window');
    issueWindow.classList.add('visible');

    const overlay = document.getElementById('github-issue-background-overlay');
    overlay.classList.add('visible');
}

function closeSubmitIssueWindow() {
    const issueWindow = document.getElementById('github-issue-window');
    issueWindow.classList.add('box-explode');
    issueWindow.addEventListener('animationend', function hideWindow() {
        issueWindow.classList.remove('visible');
        issueWindow.classList.remove('box-explode');
        issueWindow.removeEventListener('animationend', hideWindow);
    });

    const overlay = document.getElementById('github-issue-background-overlay');
    overlay.classList.add('fade-out');
    overlay.addEventListener('animationend', function hideOverlay() {
        overlay.classList.remove('visible');
        overlay.classList.remove('fade-out');
        overlay.removeEventListener('animationend', hideOverlay);
    });

}
