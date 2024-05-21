document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('a.nav-link').forEach(function(link) {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            const url = link.getAttribute('data-url');
            fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.text())
            .then(data => {
                document.getElementById('main-content').innerHTML = data;
                history.pushState(null, '', url);
            });
        });
    });

    window.addEventListener('popstate', function() {
        const url = window.location.pathname;
        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.text())
        .then(data => {
            document.getElementById('main-content').innerHTML = data;
        });
    });
});
