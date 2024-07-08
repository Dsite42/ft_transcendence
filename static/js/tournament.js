function updatePageWithTournamentDataJson(tournamentData) {
    console.log(gettext('Updating page with tournament data:'), tournamentData);
    let matchesHtml = '';
    if (tournamentData.matches && tournamentData.matches.length > 0) {
        matchesHtml = `<div class="matches"><h2>${gettext('Matches:')}</h2>`;
        tournamentData.matches.forEach(match => {
            matchesHtml += `
                <div class="match">
                    <p>
                        <span>${gettext('Players:')} ${tournamentData.display_names[match.players[0]]} ${gettext('vs')} ${tournamentData.display_names[match.players[1]]}</span> |
                        <span>${gettext('Status:')} ${match.status}</span> |
                        <span>${gettext('Winner:')} ${tournamentData.display_names[match.winner] || gettext('N/A')}</span>
                    </p> 
                </div>
            `;
        });
        matchesHtml += '</div>';
    }

    let tournamentWinnerHtml = '';
    if (tournamentData.status == 'ended') {
        tournamentWinnerHtml = `<h2>${gettext('And the Tournament winner is:')} <span style="color: blue;">${tournamentData.display_names[tournamentData.winner]}</span></h2> <h2> ${gettext('Congratulations!')}</h2>`;    }

    document.getElementById('main-content').innerHTML = `
    <div class="container mt-5 text-center">
        <h1>${gettext('Welcome to Tournament:')} <em>${tournamentData.name}</em></h1>
        <p>${gettext('Creator:')} ${tournamentData.display_names[tournamentData.creator]}</p>
        <p>${gettext('Number of Players joined:')} ${tournamentData.players.length} / ${tournamentData.number_of_players}</p>
        <p>${gettext('Players joined:')} ${tournamentData.players.map(player => tournamentData.display_names[player]).join(', ')}</p>
        <p>${gettext('Status:')} ${tournamentData.status}</p>
        ${matchesHtml}
        ${tournamentWinnerHtml}
        </div>   
        `;
}

function updatePageTournamentAborted() {
    document.getElementById('main-content').innerHTML = `
    <div class="container mt-5 text-center">
        <h1>${gettext('Tournament has been aborted')}</h1>
        <p> ${gettext('A player has left the tournament.')}</p>
    </div>
    `;
}