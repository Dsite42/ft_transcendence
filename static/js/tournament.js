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
    console.log('Updating page with tournament data:', tournamentData);
    let matchesHtml = '';
    if (tournamentData.matches && tournamentData.matches.length > 0) {
        matchesHtml = '<div class="matches"><h2>Matches:</h2>';
        tournamentData.matches.forEach(match => {
            matchesHtml += `
                <div class="match">
                    <p>
                        <span>Players: ${match.players.join(' vs ')}</span> |
                        <span>Status: ${match.status}</span> |
                        <span>Winner: ${match.winner || 'N/A'}</span>
                    </p> 
                </div>
            `;
        });
        matchesHtml += '</div>';
    }

    document.getElementById('main-content').innerHTML = `
    <div class="container mt-5 text-center">
        <h1>Welcome to Tournament: ${tournamentData.name}</h1>
        <p>Creator: ${tournamentData.creator}</p>
        <p>Number of Players joined: ${tournamentData.players.length} / ${tournamentData.number_of_players}</p>
        <p>Status: ${tournamentData.status}</p>
        <p>Players: ${tournamentData.players.join(', ')}</p>
        ${matchesHtml}
    </div>
    `;
}