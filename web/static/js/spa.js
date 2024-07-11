var chart;
document.addEventListener('DOMContentLoaded', function() {
    // Block the screen for 2FA if activated and not authenticated
    blockScreenFor2FA();
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
                if (chart) {
                    chart.destroy();
                }
                // Update the desired object with the fetched content
                const targetObject = document.getElementById('main-content'); // Replace 'learn-content' with the ID of the object
                if (targetObject) {
                    targetObject.innerHTML = data;
                    const scriptElements = targetObject.getElementsByTagName('script');
                    for (let index = 0; index < scriptElements.length; index++)
                        eval(scriptElements[index].innerHTML);
                } else {
                    console.error("Target object not found");
                }
                
                // Optionally, update the URL in the address bar
                history.pushState(null, '', url);
                
                // Call the updatePendingFriendRequests function if a session token is set
                if (document.cookie.split(';').some((item) => item.trim().startsWith('session='))) {
                    checkPendingFriendRequests();
                }
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
            if (chart) {
                chart.destroy();
            }
             // Call the updatePendingFriendRequests function if a session token is set
             if (document.cookie.split(';').some((item) => item.trim().startsWith('session='))) {
                checkPendingFriendRequests();
            }
            // Update the desired object with the fetched content
            const targetObject = document.getElementById('main-content'); // Replace 'learn-content' with the ID of the object
            if (targetObject) {
                targetObject.innerHTML = data;
                const scriptElements = targetObject.getElementsByTagName('script');
                for (let index = 0; index < scriptElements.length; index++)
                    eval(scriptElements[index].innerHTML);
            } else {
                console.error("Target object not found");
            }
        })
        .catch(error => {
            console.error("Error fetching data:", error);
        });
    });
    
});

function generate_otp_QR()
{
    console.log('Button clicked');
    fetch('/enable_otp/')
        .then(response => {
            console.log('Received response', response);
            return response.json();
        })
        .then(data => {
            const img = document.getElementById('qr-code');
            img.src = 'data:image/png;base64,' + data.qr_code;
            img.style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function send_otp_code()
{
    const otp = document.getElementById('otp-input').value;
        
    fetch('/verify_otp/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ otp: otp })
    })
    .then(response => response.text())
    .then(data => {
        if (data === 'OTP is valid') {
            alert(gettext('OTP is valid!'));
    
        }
        else
        {
            alert(gettext('Invalid OTP!'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });

}

function getCookie(name){

    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


function changeInfoSave() {
    const avatarUrlField = document.getElementById('avatarUrl');
    const avatarFileField = document.getElementById('avatarFile');
    const formData = new FormData();
    formData.append('displayName', document.getElementById('displayName').value);
    if (avatarFileField.files[0]) {
        formData.append('avatarFile', avatarFileField.files[0]);
    }
    if (avatarUrlField.value) {
        formData.append('avatarUrl', avatarUrlField.value);
    }
    fetch('/change_info/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
    .then(response => response.json())
    .then(response => {
        if (response.success) {
            alert(gettext('Info changed successfully, refresh site for avatar changes to take effect!'));
        } else {
            alert(gettext('Error changing info! : ') +response.reason);
        }
    });
}

function addFriend(event) {

    event.preventDefault();
   
    var formData = new FormData(event.target);

    
    fetch('/send_friend_request/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {

        if (data.success) {
            alert(gettext('Friend request sent successfully!'));
        } else {
            alert(gettext('Error sending friend request: ') + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert(gettext('An error occurred while sending the friend request.'));
    });
}

function acceptFriendRequest(userIntraName, friendUsername) {
    fetch('/accept_friend_request/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')  
        },
        body: 'user_intra_name=' + userIntraName + '&friend_username=' + friendUsername
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(gettext('Friend request accepted successfully!'));
            window.location.reload();
        }
    });
}

function declineFriendRequest(userIntraName, friendUsername) {
    fetch('/decline_friend_request/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')  
        },
        body: 'user_intra_name=' + userIntraName + '&friend_username=' + friendUsername + '&remove=false'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(gettext('Friend request declined successfully!'));
            window.location.reload();
        }
    });
}

function removeFriend(userIntraName, friendUsername) {
    fetch('/decline_friend_request/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')  
        },
        body: 'user_intra_name=' + userIntraName + '&friend_username=' + friendUsername + '&remove=true'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(gettext('Friend removed successfully!'));
            window.location.reload();
        }
    });
}

function checkPendingFriendRequests() {
    fetch('/get_pending_friend_requests/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')  
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.length > 0) {
            alert(gettext('You have a pending friend requests, refresh the site in order to see it!'));
        }
    });
}

// Game Functions   

function drawLoadingScreen() {

    canvas = document.getElementById('gameCanvas');
    const context = canvas.getContext('2d');

    // Clear the canvas
    context.clearRect(0, 0, canvas.width, canvas.height);

    // Fill the canvas with black
    context.fillStyle = 'black';
    context.fillRect(0, 0, canvas.width, canvas.height);

    // Set the font and alignment
    context.font = '30px Arial';
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.fillStyle = 'white';
    // Draw the loading text
    context.fillText('Loading...', canvas.width / 2, canvas.height / 2);
}

function drawErrorScreen(error) {

    canvas = document.getElementById('gameCanvas');
    const context = canvas.getContext('2d');

    // Clear the canvas
    context.clearRect(0, 0, canvas.width, canvas.height);

    // Fill the canvas with black
    context.fillStyle = 'black';
    context.fillRect(0, 0, canvas.width, canvas.height);

    // Set the font and alignment
    context.font = '30px Arial';
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.fillStyle = 'white'; 

    // Draw the loading text
    context.fillText('Error: ' + error, canvas.width / 2, canvas.height / 2);
}


// Set the functions called on game Events

Game.onLoading = drawLoadingScreen;
Game.onError = drawErrorScreen;



// Function to block the screen if 2FA is activated and not authenticated



// Function to decode JWT
function decodeJWT(session) {
    try {
        const data = jwt_decode(session); // Use jwt_decode from the included library
        return data;
    } catch (err) {
        console.error('Failed to decode JWT:', err);
        return null;
    }
}
    // Function to get a specific cookie value by name
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    // Function to send OTP code for login
    function send_otp_code_login(event) {
        event.preventDefault(); // Prevent form submission

        const otp = document.getElementById('otp-input').value;

        fetch('/login_with_otp/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ otp: otp })
        })
        .then(response => response.text())
        .then(data => {
            
             if (data === 'OTP is valid') {
                alert(gettext('OTP is valid!'));
                const overlay = document.getElementById('2fa-overlay');
                if (overlay) {
                    overlay.remove();
            }
            }
            else
            {
                alert(gettext('Invalid OTP!'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }

    // Function to create and display the OTP form
    function createOtpForm() {
        // Create form
        const form = document.createElement('form');
        form.id = 'otp-form';
        form.onsubmit = send_otp_code_login;

        // Create form elements
        const title = document.createElement('h2');
        title.textContent = gettext('Enter OTP Code');

        const input = document.createElement('input');
        input.type = 'text';
        input.id = 'otp-input';
        input.placeholder = gettext('Enter OTP');
        input.required = true;

        const button = document.createElement('button');
        button.type = 'submit';
        button.id = 'otp-submit';
        button.textContent = gettext('Submit');

        // Append elements to form
        form.appendChild(title);
        form.appendChild(input);
        form.appendChild(button);

        // Style the form
        form.style.backgroundColor = 'white';
        form.style.padding = '20px';
        form.style.borderRadius = '10px';
        form.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.5)';
        form.style.textAlign = 'center';

        // Append form to overlay
        const overlay = document.getElementById('2fa-overlay');
        overlay.appendChild(form);
    }

    // Function to block the screen for 2FA
    function blockScreenFor2FA() {
        // Get the session cookie
        const sessionCookie = getCookie('session');
        if (!sessionCookie) {
            return;
        }

        // Decode the session cookie
        const sessionData = decodeJWT(sessionCookie);
        if (!sessionData) {
            console.error('Failed to decode session cookie');
            return;
        }

        // Check if 2FA is activated and not passed
        const is2FAActivated = sessionData['2FA_Activated'] === true;
        const is2FAPassed = sessionData['2FA_Passed'] === true;

        if (is2FAActivated && !is2FAPassed) {
            // Create the overlay
            const overlay = document.createElement('div');
            overlay.id = '2fa-overlay';
            overlay.style.position = 'fixed';
            overlay.style.top = '0';
            overlay.style.left = '0';
            overlay.style.width = '100%';
            overlay.style.height = '100%';
            overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
            overlay.style.zIndex = '10000';
            overlay.style.display = 'flex';
            overlay.style.justifyContent = 'center';
            overlay.style.alignItems = 'center';

            // Append the overlay to the body
            document.body.appendChild(overlay);
            
            createOtpForm();
        }
    }
