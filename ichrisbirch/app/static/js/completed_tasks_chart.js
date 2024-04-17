const labels = JSON.parse(document.getElementById('chartLabels').textContent);
const data = JSON.parse(document.getElementById('chartValues').textContent);
const textColor = 'hsl(0 0% 85%)';
const gridColor = 'hsl(0 0% 35%)';
const maxDataValue = Math.max(...data);
const backgroundColor = [
    'rgba(255, 99, 132, 0.2)',
    'rgba(255, 159, 64, 0.2)',
    'rgba(255, 205, 86, 0.2)',
    'rgba(75, 192, 192, 0.2)',
    'rgba(54, 162, 235, 0.2)',
    'rgba(153, 102, 255, 0.2)',
    'rgba(201, 203, 207, 0.2)'
];
const scales = {
    y: {
        beginAtZero: true,
        max: Math.ceil(maxDataValue * 1.3),
        grid: {
            color: gridColor,
            // borderColor: gridColor,
        },
        ticks: {
            color: textColor,
            stepSize: 1,
            font: {
                size: 20
            }
        }
    },
    x: {
        grid: {
            // color: gridColor,
            borderColor: gridColor,
        },
        ticks: {
            color: textColor,
            font: {
                size: 20
            }
        }
    }
};
const options = {
    scales: scales,
    layout: {
        padding: {
            left: 20,
            right: 20,
            bottom: 20
        }
    },
    plugins: {
        legend: {
            display: false
        },
        title: {
            display: true,
            text: 'Completed Tasks',
            color: textColor,
            font: {
                size: 20
            },
            padding: 40
        }
    }
};
const config = {
    type: 'bar',
    data: {
        labels: labels,
        datasets: [
            {
                label: "Completed Tasks",
                data: data,
                backgroundColor: backgroundColor
            }
        ]
    },
    options: options
};
var ctx = document.getElementById("completedChart").getContext("2d");
var barChart = new Chart(ctx, config);
