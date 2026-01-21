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
const wsUrl = `${wsProtocol}//${apiHost}/admin/log-stream/`;
console.log('Connecting to WebSocket:', wsUrl);
var ws_log = new WebSocket(wsUrl);

ws_log.onopen = function () {
    console.log('WebSocket connected');
    const logs = document.getElementById("logs");
    const statusDiv = document.createElement("div");
    statusDiv.innerHTML = '<span style="color: green;">Connected to log stream...</span>';
    logs.appendChild(statusDiv);
};

ws_log.onmessage = function (event) {
    const newElement = document.createElement("div");
    var logs = document.getElementById("logs");
    newElement.innerHTML = formatAndColorizeLog(event.data);
    logs.appendChild(newElement);
    // Scroll to the bottom
    logs.scrollTop = logs.scrollHeight;
};

ws_log.onerror = function (error) {
    console.error('WebSocket error:', error);
    const logs = document.getElementById("logs");
    const errorDiv = document.createElement("div");
    errorDiv.innerHTML = '<span style="color: red;">WebSocket error - check browser console</span>';
    logs.appendChild(errorDiv);
};

ws_log.onclose = function (event) {
    console.log('WebSocket closed:', event.code, event.reason);
    const logs = document.getElementById("logs");
    const closeDiv = document.createElement("div");
    closeDiv.innerHTML = `<span style="color: orange;">Connection closed (code: ${event.code})</span>`;
    logs.appendChild(closeDiv);
};
