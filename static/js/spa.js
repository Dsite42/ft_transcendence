document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('a.nav-link').forEach(function(link) {
        link.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent the default link behavior
            
            const url = link.getAttribute('href'); // Get the URL from the link's href attribute
            console.log("Fetching data from:", url);
            
            // Fetch the content of the page using the URL
            urlnew = url.replace("#", "");
            urlnew = urlnew + ".html"
            fetch(urlnew, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.text())
            .then(data => {
                console.log("Received data:", data);
                
                // Update the desired object with the fetched content
                const targetObject = document.getElementById('main-content'); // Replace 'learn-content' with the ID of the object
                if (targetObject) {
                    targetObject.innerHTML = data;
                } else {
                    console.error("Target object not found");
                }
                
                // Optionally, update the URL in the address bar
                history.pushState(null, '', url);
            })
            .catch(error => {
                console.error("Error fetching data:", error);
            });
        });
    });

      // Event listener for when the user navigates backward or forward
      window.addEventListener('popstate', function(event) {
        console.log("Popstate event triggered.");
        
        // Fetch the content of the previous or next page
        const url = window.location.href;

        urlnew = url.replace("#", "");
        urlnew = urlnew + ".html";
        console.log("Fetching data from:", urlnew);
        fetch(urlnew, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.text())
        .then(data => {
            console.log("Received data:", data);
            
            // Update the desired object with the fetched content
            const targetObject = document.getElementById('main-content'); // Replace 'learn-content' with the ID of the object
            if (targetObject) {
                targetObject.innerHTML = data;
            } else {
                console.error("Target object not found");
            }
        })
        .catch(error => {
            console.error("Error fetching data:", error);
        });
    });
    
});
