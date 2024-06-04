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

function generate_otp_QR()
{
    console.log('Button clicked');
    fetch('/enable_otp/')
        .then(response => {
            console.log('Received response', response);
            return response.json();
        })
        .then(data => {
            console.log('Received data', data);
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
        console.log('Received data', data);
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
        console.log('Received data', data);
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
            alert('Info changed successfully, refresh site for avatar changes to take effect!');
        } else {
            alert('Error changing info! : ' +response.reason);
        }
    });
}

function addFriend(event) {
    // Prevent the form from being submitted normally
    event.preventDefault();

    // Get the form data
    var formData = new FormData(event.target);

    // Send the form data to the server
    fetch('/send_friend_request/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')  // Django requires the CSRF token to be included in the request header
        }
    })
    .then(response => response.json())
    .then(data => {
        // Handle the response from the server
        if (data.success) {
            alert('Friend request sent successfully!');
        } else {
            alert('Error sending friend request: ' + data.error);
        }
    })
    .catch(error => {
        // Handle any errors
        console.error('Error:', error);
        alert('An error occurred while sending the friend request.');
    });
}