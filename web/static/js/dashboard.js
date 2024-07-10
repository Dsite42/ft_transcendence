var chart;

// Function to populate the table
function populateTable(data, tag) {
    // Initialize Bootstrap Table with data
    $(tag).bootstrapTable('destroy').bootstrapTable({
        data: data,
        sortable: true,
        onClickRow: function(row, $element, field) {
            if (tag == '#player-table')
                createDetailChart(row);
            else if (tag == '#tournament-table') {
                alert('Clicked on row: ' + row.id);
                join_tournament(row.id);
            }
        }
    });
}


// Function to filter the table by user
function filterTableByUser(username) {
    const table = $('#game_sessions-table');
    const data = table.bootstrapTable('getData');
    const filteredData = data.filter(session => session.player1 === username || session.player2 === username);
    populateTable(filteredData, '#game_sessions-table');
    return filteredData;
}

// Function to create the detail chart
function createDetailChart(player) {
    if (chart) {
        chart.destroy();
    }
    const names = [gettext('Wins'), gettext('Losses')];
    const wins = [player.games_won, player.games_lost];
    var options = {
        title: {
            text: gettext('Wins'),
            align: 'center',
            style: {
                fontSize: '30px',
                fontWeight: 'bold',
                fontFamily: undefined,
                color: '#263238'
            }
        },
        chart: {
            type: 'pie'
        },
        series: wins,
        labels: names,
        responsive: [{
            breakpoint: 480,
            options: {
                chart: {
                    width: 10
                },
                legend: {
                    position: 'bottom'
                }
            }
        }]
    };
    chart = new ApexCharts(document.querySelector("#chart-player-table"), options);
    chart.render();
}


function prepareDataForGameSessionChart(data) {
    // Prepare data for stepline chart
    // Aggregate games by date
    var gamesByDate = data.reduce((acc, session) => {
        // Extract just the date part from the 'date' string
        let date = session.date.split(' ')[0];
        if (acc[date]) {
            acc[date] += 1;
        } else {
            acc[date] = 1;
        }
        return acc;
    }, {});

    // Get the range of dates
    let dates = Object.keys(gamesByDate);
    let minDate = new Date(Math.min(...dates.map(date => new Date(date).getTime())));
    let maxDate = new Date();

    // Fill in missing dates with zero
    let currentDate = minDate;
    while (currentDate <= maxDate) {
        let dateString = currentDate.toISOString().split('T')[0];
        if (!gamesByDate[dateString]) {
            gamesByDate[dateString] = 0;
        }
        currentDate.setDate(currentDate.getDate() + 1);
    }

    // Transform data for ApexCharts
    var chartData = Object.entries(gamesByDate).map(([date, count]) => ({
        x: new Date(date).getTime(), // Convert date string to timestamp
        y: count
    }));

    // Sort data by date as ApexCharts expects data to be sorted for time series
    chartData.sort((a, b) => a.x - b.x);
    return chartData;
}

function createGameSessionChart(data) {
    if (chart) {
        chart.destroy();
    }
    var options = {
        series: [{
            data: data
        }],
        chart: {
            type: 'line',
            height: 350
        },
        stroke: {
            curve: 'stepline',
        },
        dataLabels: {
            enabled: false
        },
        title: {
            text: gettext('Amount of matches over time'),
            align: 'left'
        },
        markers: {
            hover: {
                sizeOffset: 4
            }
        },
        xaxis: {
            type: 'datetime',
            labels: {
                format: 'dd MMM'
            }
        }
    };

      chart = new ApexCharts(document.querySelector("#chart-game_sessions"), options);
      chart.render();
}