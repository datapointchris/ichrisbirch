function formatAndColorizeLog(logLine) {
    // Match structlog's ConsoleRenderer format: [level    ] (lowercase, padded to 9 chars)
    const logLevels = {
        'debug': 'green',
        'info': 'lightblue',
        'warning': 'yellow',
        'error': 'red',
        'critical': 'magenta'
    };

    let formattedLog = logLine;

    // Match pattern like [info     ] or [warning  ] (level in brackets with optional padding)
    const levelRegex = /\[(debug|info|warning|error|critical)(\s*)\]/i;
    const match = logLine.match(levelRegex);

    if (match) {
        const level = match[1].toLowerCase();
        const padding = match[2].replace(/ /g, '&nbsp;'); // Preserve spaces in HTML
        const color = logLevels[level];
        if (color) {
            const coloredLevel = `<span style="color: ${color};">[${match[1]}${padding}]</span>`;
            formattedLog = logLine.replace(match[0], coloredLevel);
        }
    }

    return formattedLog;
}
// WEBSOCKETS
// Use the current page's protocol (wss for https, ws for http) and derive API host from app host
const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const apiHost = window.location.hostname.replace('app.', 'api.');
var ws_log = new WebSocket(`${wsProtocol}//${apiHost}/admin/log-stream/`);

ws_log.onmessage = function (event) {
    const newElement = document.createElement("div");
    var logs = document.getElementById("logs");
    newElement.innerHTML = formatAndColorizeLog(event.data);
    logs.appendChild(newElement);
    // Scroll to the bottom
    logs.scrollTop = logs.scrollHeight;
};
