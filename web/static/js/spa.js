var chart;
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
        alert(data);
        if (data === 'OTP is valid') {
            window.location.href = '/';
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });

}

function send_otp_code_login()
{
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
        alert(data);
        if (data === 'OTP is valid') {
            window.location.href = '/';
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

function component(tag, attributes, ...next) {
    const element = document.createElement(tag);
    for (const [key, value] of Object.entries(attributes)) {
        if (key === 'class')
            element.className = value;
        else if (key.startsWith('on'))
            element[key] = value;
        else
            element.setAttribute(key, value);
    }
    if (next.length === 1 && typeof next[0] === 'string')
        element.textContent = next[0];
    else
        element.replaceChildren(...next);
    return element;
}

function refreshFriends() {
    fetch('/get_friends/')
        .then(response => response.json())
        .then(data => {
            const button = document.getElementById('friends_button');
            button.replaceChildren(component('span', {}, gettext('Friends') + ' '));
            if (data.pending_friends.length > 0)
                button.appendChild(component('span', {'class': 'badge bg-danger'}, data.pending_friends.length.toString()));
            const friendList = document.getElementById('friend_list');
            friendList.replaceChildren(
                ...(data.friends.length === 0
                        ? [component('li', {'class': 'list-group-item'}, gettext('No friends yet:'))]
                        : data.friends.map(friend => component('li', {'class': 'list-group-item d-flex align-items-center justify-content-between'},
                            component('div', {},
                                component('span', {}, friend.username),
                                component('p', {'class': 'mb-0'},
                                    component('small', {}, Date.now() - (new Date(friend.last_active).getTime()) > 300000
                                        ? (gettext('Last online:') + ' ' + friend.last_active)
                                        : gettext('Online')
                                    )
                                )
                            ),
                            component('div', {},
                                component('button', {'class': 'btn btn-danger btn-sm', 'onclick': () => { removeFriend(friend.username); }},
                                    gettext('Remove')
                                )
                            )
                        )
                    )
                ),
                component('hr', {}),
                component('br', {}),
                component('h5', {}, gettext('Pending Friend Requests')),
                component('div', {},
                    ...data.pending_friends.map(pendingFriend => 
                        component('li', { 'class': 'list-group-item d-flex align-items-center justify-content-between' },
                            component('div', {}, pendingFriend.username + ' ' + gettext('(Pending)'),
                                component('button', {'class': 'btn btn-success btn-sm', 'onclick': () => { acceptFriendRequest(pendingFriend.username); }},
                                    gettext('Accept')
                                ),
                                component('button', {'class': 'btn btn-danger btn-sm', 'onclick': () => { declineFriendRequest(pendingFriend.username); }},
                                    gettext('Decline')
                                )
                            )
                        )
                    )
                )
            );
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

function acceptFriendRequest(friendUsername) {
    fetch('/accept_friend_request/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')  
        },
        body: 'friend_username=' + friendUsername
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(gettext('Friend request accepted successfully!'));
            refreshFriends();
        }
    });
}

function declineFriendRequest(friendUsername) {
    fetch('/decline_friend_request/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')  
        },
        body: 'friend_username=' + friendUsername + '&remove=false'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(gettext('Friend request declined successfully!'));
            refreshFriends();
        }
    });
}

function removeFriend(friendUsername) {
    fetch('/decline_friend_request/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')  
        },
        body: 'friend_username=' + friendUsername + '&remove=true'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(gettext('Friend removed successfully!'));
            refreshFriends();
        }
    });
}

function checkPendingFriendRequests() {
    refreshFriends();
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


