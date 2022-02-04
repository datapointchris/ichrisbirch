
var movingDate = new Date("Dec 26, 2021 00:00:00").getTime();
var cognizantDate = new Date("Oct 1, 2022 00:00:00").getTime();
var talentpathDate = new Date("Mar 1, 2023 00:00:00").getTime();
// Update the count down every 1 second (1000 at the end)

function calculateDays(deadline, id) {
    var deadlineDate = new Date(deadline).getTime();
    var daysUntil = setInterval(function () {
        var now = new Date().getTime();
        var distance = deadlineDate - now;
        var days = Math.floor(distance / (1000 * 60 * 60 * 24));
        document.getElementById(id).innerHTML = days
        if (days < 31) {
            document.getElementById(id).style.color = "green";
        }
        if (days < 8) {
            document.getElementById(id).style.color = "darkred";
        }
    }, 1000);
}