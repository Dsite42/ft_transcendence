
// Function to populate the table
function populateTable(data, tag) {
    // Initialize Bootstrap Table with data
    $(tag).bootstrapTable('destroy').bootstrapTable({
        data: data,
        sortable: true,
        onClickRow: function(row, $element, field) {
            if (tag == '#player-table')
                createDetailChart(row);
            else if (tag == '#game_sessions-table')
                createDetailSessionChart(row);
        }
    });
}

// Function to filter the table by user
function filterTableByUser(username) {
    const table = $('#game_sessions-table');
    const data = table.bootstrapTable('getData');
    const filteredData = data.filter(session => session.player1 === username || session.player2 === username);
    populateTable(filteredData, '#game_sessions-table');
}

// Function to create the detail chart
function createDetailChart(player) {
    if (chart) {
        chart.destroy();
    }
    const names = ['Wins', 'Losses'];
    const wins = [player.games_won, player.games_lost];
    var options = {
        title: {
            text: 'Wins',
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


// Function to create the detail chart
function createDetailSessionChart(session) {
    if (chart) {
        chart.destroy();
    }
    const names = [session.player1, session.player2];
    const wins = [session.player1_score, session.player2_score];
    var options = {
        title: {
            text: 'Player Scores',
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
    chart = new ApexCharts(document.querySelector("#chart-game_sessions"), options);
    chart.render();
}
