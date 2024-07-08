function fetchTournamentData(tournamentId) {
    fetch(`api/tournament/${tournamentId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Tournament data:', data);
            updatePageWithTournamentData(data);
        })
        .catch(error => console.error('Failed to fetch tournament data:', error));
}

function updatePageWithTournamentData(tournamentData) {
    document.getElementById('main-content').innerHTML = `
    <div class="container mt-5 text-center">
        <h1> Welcome to Tournament: ${tournamentData.name} </h1>
        <br> Creator: ${tournamentData.creator} </br>
        <br> Number of Players joined: ${tournamentData.players.length} / ${ tournamentData.number_of_players} </br>
        <br> Status: ${tournamentData.status} </br>
        <br> Players: ${tournamentData.players.join(', ')} </br>
    </div>
    `;
}
