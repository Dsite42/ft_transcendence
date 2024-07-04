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
        <h1>Welcome to Tournament: <em>${tournamentData.name}</em></h1>
        <p>Creator: ${tournamentData.creator}</p>
        <p>Number of Players joined: ${tournamentData.players.length} / ${tournamentData.number_of_players}</p>
        <p>Status: ${tournamentData.status}</p>
        <p>Players: ${tournamentData.players.join(', ')}</p>
        ${matchesHtml}
    </div>
    `;
}

function updatePageWithTournamentDataJson(tournamentData) {
    console.log('Updating page with tournament data:', tournamentData);
    let matchesHtml = '';
    if (tournamentData.matches && tournamentData.matches.length > 0) {
        matchesHtml = '<div class="matches"><h2>Matches:</h2>';
        tournamentData.matches.forEach(match => {
            matchesHtml += `
                <div class="match">
                    <p>
                        <span>Players: ${tournamentData.display_names[match.players[0]]} vs ${tournamentData.display_names[match.players[1]]}</span> |
                        <span>Status: ${match.status}</span> |
                        <span>Winner: ${tournamentData.display_names[match.winner] || 'N/A'}</span>
                    </p> 
                </div>
            `;
        });
        matchesHtml += '</div>';
    }

    let tournamentWinnerHtml = '';
    if (tournamentData.status == 'ended') {
        tournamentWinnerHtml = `<h2>And the Tournament winner is: <span style="color: blue;">${tournamentData.display_names[tournamentData.winner]}</span></h2> <h2> Congratulations!</h2>`;    }

    document.getElementById('main-content').innerHTML = `
    <div class="container mt-5 text-center">
        <h1>Welcome to Tournament: <em>${tournamentData.name}</em></h1>
        <p>Creator: ${tournamentData.display_names[tournamentData.creator]}</p>
        <p>Number of Players joined: ${tournamentData.players.length} / ${tournamentData.number_of_players}</p>
        <p>Status: ${tournamentData.status}</p>
        ${matchesHtml}
        ${tournamentWinnerHtml}
        </div>   
        `;
        //<p>Players: ${tournamentData.display_names.join(', ')}</p>
}