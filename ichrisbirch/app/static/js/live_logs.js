function formatAndColorizeLog(logLine) {
    const logLevels = {
        '[DEBUG]': { color: 'green', length: 7 },
        '[INFO]': { color: 'lightblue', length: 6 },
        '[WARNING]': { color: 'yellow', length: 9 },
        '[ERROR]': { color: 'red', length: 7 },
        '[CRITICAL]': { color: 'magenta', length: 10 } // longest length including brackets
    };

    let formattedLog = logLine;
    let maxLevelLength = Math.max(...Object.values(logLevels).map(level => level.length));

    for (const [level, { color, length }] of Object.entries(logLevels)) {
        if (logLine.includes(level)) {
            const paddingNeeded = '&nbsp;'.repeat(maxLevelLength - length);
            const coloredLevel = `<span style="color: ${color};">${level}${paddingNeeded}</span>`;
            formattedLog = logLine.replace(level, coloredLevel);
            break; // Assume only one log level per line and stop searching once found
        }
    }

    return formattedLog;
}
// WEBSOCKETS
const apiHost = document.getElementById('apiHost').textContent;
const apiPort = document.getElementById('apiPort').textContent;
var ws_log = new WebSocket(`ws://${apiHost}:${apiPort}/admin/log-stream/`);

ws_log.onmessage = function (event) {
    const newElement = document.createElement("div");
    var logs = document.getElementById("logs");
    newElement.innerHTML = formatAndColorizeLog(event.data);
    logs.appendChild(newElement);
    // Scroll to the bottom
    logs.scrollTop = logs.scrollHeight;
};
