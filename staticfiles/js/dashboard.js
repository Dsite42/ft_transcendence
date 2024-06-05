var chart;

// Function to fetch data from the backend
async function fetchPlayerRanking() {
    return fetch('/fetch_players/')
        .then(response => response.json())
        .then(data => {
            console.log('Fetched Data:', data);
            populateTable(data);
            return data;
        });
}
// Function to populate the table
function populateTable(data) {
    // Initialize Bootstrap Table with data
    $('#player-table').bootstrapTable('destroy').bootstrapTable({
        data: data,
        sortable: true,
        onClickRow: function(row, $element, field) {
            createDetailChart(row);
        }
    });
}
// Function to create the detail chart
function createDetailChart(player) {
    if (chart) {
        chart.destroy();
    }
    const names = ['Wins', 'Losses'];
    const wins = [player.wins, player.losses];
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
    chart = new ApexCharts(document.querySelector("#chart-details"), options);
    chart.render();
}
// Fetch data and populate table
fetchPlayerRanking();

