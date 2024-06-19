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
                console.log("Received data:", data);
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
            console.log("Received data:", data);
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


// Game logic
'use strict'
const Game = (() => {
    const game = {
        onLoading: null,
        onRunning: null,
        onFinish: null,
        onError: null,

        start: async (canvas, host, tokens) => {
            // Prevent asynchonous race conditions
            if (mStatus !== kStatus_None && mStatus !== kStatus_Finished && mStatus !== kStatus_Error)
                throw errorWithMessage('Attempt to start game multiple times');
            mStatus = kStatus_Loading;
            try {
                game.onLoading && game.onLoading();
            } catch {}

            try {
                // Determine the game socket's address
                if (location.protocol !== 'https:' && location.protocol !== 'http:')
                    throw errorWithMessage('Unsupported protocol');
                let address = location.protocol.replace('http', 'ws')
                    .concat(
                        '//', host, '/game',
                        ...tokens.map((token, index) =>
                            `${index === 0 ? "?" : "&"}with_token=${token}`
                        )
                    );

                // Get a 2D drawing context
                mCanvas = canvas;
                mContext = canvas.getContext('2d');
                if (mContext === null || mContext === undefined)
                    throw errorWithMessage('Unable to get 2D drawing context');

                // Reset input and interpolation state
                mInputState = 0;
                mLastInputState = 0;
                mReadyCallback = null;
                mLastUpdateTime = null;
                mNextUpdateTime = null;
                mAverageUpdateDelta = null;

                // Try to connect to the game server
                await new Promise((resolve, reject) => {
                    const timeout = setTimeout(() => {
                        reject(errorWithMessage('Timeout during connection attempt'));
                        try {
                            mSocket.close();
                        } catch {}
                    }, 2500);

                    mSocket = new WebSocket(address);
                    mSocket.binaryType = 'arraybuffer';
                    mSocket.onmessage = event => {
                        clearTimeout(timeout);
                        resolve(mSocket);
                        onSocketMessage(event);
                    };
                    mSocket.onclose = () => {
                        clearTimeout(timeout);
                        reject(errorWithMessage('Unable to connect to server'));
                    };
                });
                mSocket.onmessage = onSocketMessage;
                mSocket.onclose = null;

                // Wait for the ready callback
                await new Promise((resolve, reject) => {
                    const timeout = setTimeout(() => {
                        mSocket.onmessage = null;
                        mSocket.onclose = null;
                        try {
                            mSocket.close();
                        } catch {}
                        reject(errorWithMessage('Server is not responding'));
                    }, 1000);

                    mSocket.onclose = () => {
                        reject(errorWithMessage('Connection to server was lost'));
                    };
                    mReadyCallback = () => {
                        clearTimeout(timeout);
                        resolve();
                    };
                });

                if (mPhase == kPhase_Finished) {
                    // The game is already finished, close the socket and transition into finished state
                    mStatus = kStatus_Finished;
                    try {
                        game.onFinish && game.onFinish(mScoreA, mScoreB);
                    } catch {}
                    try {
                        mSocket.close();
                    } catch {}
                } else {
                    // Bind events and start animating
                    mSocket.onclose = onSocketClose;
                    addEventListener('keyup', onKeyUp);
                    addEventListener('keydown', onKeyDown);
                    requestAnimationFrame(onAnimationFrame);
                }
            } catch (error) {
                mStatus = kStatus_Error;
                try {
                    if (error instanceof Error && error.withMessage === true)
                        game.onError && game.onError(error.message);
                    else
                        game.onError && game.onError('Unable to start game');
                } catch {}
            }
        }
    };

    // Constants; these should match with the server's code
    const kPhase_Waiting = 0, kPhase_Playing = 1, kPhase_Intermission = 2, kPhase_Finished = 3;
    const kStatus_None = 0, kStatus_Loading = 1, kStatus_Running = 2, kStatus_Finished = 3, kStatus_Error = 4;
    const kWorldAspect = 4.0 / 3.0, kWorldHeight = 40.0, kWorldWidth = kWorldHeight * kWorldAspect, kPaddleHeight = 8.0;

    // Input mapping
    const kButton_PrimaryUp = 1 << 0, kButton_PrimaryDown = 1 << 1, kButton_SecondaryUp = 1 << 2, kButton_SecondaryDown = 1 << 3;
    const kButtonMap = {
        'w': kButton_PrimaryUp, 's': kButton_PrimaryDown, 'ArrowUp': kButton_PrimaryUp, 'ArrowDown': kButton_PrimaryDown,
        'o': kButton_SecondaryUp, 'l': kButton_SecondaryDown
    };

    // 5x5 bitmap font for score digits (0-9)
    const kScoreFont = [
        0x0e9d72e, 0x0842988, 0x1f1322e, 0x0f83a0f,
        0x0847d4c, 0x0f83c3f, 0x0e8bc2e, 0x011111f,
        0x0e8ba2e, 0x0e87a2e
    ];

    // Resources for drawing and networking
    let mCanvas;
    let mContext;
    let mSocket;

    // Client state
    let mStatus = kStatus_None;
    let mInputState;
    let mLastInputState;
    let mReadyCallback;

    // World-to-screen transformation parameters
    let mViewClip;
    let mViewWidth;
    let mViewHeight;
    let mViewMatrix = {b: 0.0, c: 0.0};

    // Game state
    let mPhase;
    let mBallX, mBallY;
    let mScoreA, mScoreB;
    let mPaddleA, mPaddleB;

    // Game interpolation
    let mLastUpdateTime;
    let mNextUpdateTime;
    let mAverageUpdateDelta;
    let mLastBallX, mLastBallY;
    let mLastPaddleA, mLastPaddleB;
    let mNextBallX, mNextBallY;
    let mNextPaddleA, mNextPaddleB;

    /** Creates an Error object with a usable message */
    function errorWithMessage(message) {
        const error = new Error(message);
        error.withMessage = true;
        return error;
    }

    function interpolate() {
        // Calculate the interpolation time
        let time = (performance.now() - mNextUpdateTime) / mAverageUpdateDelta;
        if (time < 0.0) time = 0.0;
        if (time > 1.0) time = 1.0;

        function linear(lhs, rhs) {
            return lhs + (rhs - lhs) * time;
        }

        mBallX = linear(mLastBallX, mNextBallX);
        mBallY = linear(mLastBallY, mNextBallY);
        mPaddleA = linear(mLastPaddleA, mNextPaddleA);
        mPaddleB = linear(mLastPaddleB, mNextPaddleB);
    }

    function draw() {
        // Clear the whole frame's background
        mContext.fillStyle = '#2e2e2e';
        mContext.fillRect(0, 0, mViewWidth, mViewHeight);

        // Prepare for drawing the game world
        mContext.save();
        mContext.setTransform(mViewMatrix);
        mContext.clip(mViewClip);

        // Clear the game world's background
        mContext.fillStyle = 'black';
        mContext.fillRect(-kWorldWidth / 2.0, -kWorldHeight / 2.0, kWorldWidth, kWorldHeight);

        // Draw the dividing line
        mContext.fillStyle = 'white';
        for (let y = 0; y < Math.floor(kWorldHeight / 2.0); y++) {
            if ((y % 6) === 0) {
                mContext.fillRect(-0.1, -3.0 - y - 1.0, 0.2, 1.0);
                mContext.fillRect(-0.1,  3.0 + y,       0.2, 1.0);
            }
        }

        // Draw the ball and the paddles
        mContext.fillRect(mBallX - 0.5, mBallY - 0.5, 1.0, 1.0);
        mContext.fillRect(-kWorldWidth / 2.0, mPaddleA - kPaddleHeight / 2.0, 1.0, kPaddleHeight);
        mContext.fillRect(kWorldWidth / 2.0 - 1.0, mPaddleB - kPaddleHeight / 2.0, 1.0, kPaddleHeight);

        // Draw scores if in intermission or finished phase
        if (mPhase === kPhase_Intermission || mPhase === kPhase_Finished) {
            drawNumber(mScoreA, -kWorldWidth / 2.0 + 8.0, -3.75, 1.5, false);
            drawNumber(mScoreB, kWorldWidth / 2.0 - 8.0, -3.75, 1.5, true);
        }

        // Restore the drawing context's transform and clipping
        mContext.restore();
    }

    function drawNumber(number, x, y, scale, anchorRight) {
        // Make sure the input number is an unsigned integer which
        // is converted into an array of bitmaps to draw
        if (!Number.isInteger(number) || number < 0)
            return;
        let bitmaps = [];
        do {
            bitmaps.push(kScoreFont[number % 10]);
            number = ~~(number / 10);
        } while (number != 0);
        bitmaps.reverse();

        // Precalculate starting position, horizontal step and rectangle size
        if (anchorRight)
            x -= (bitmaps.length * 6.0 - 1.0) * scale;
        const stepX = 6.0 * scale;
        const rectSize = scale * 1.05;

        // Draw each 5x5 bitmap as a set of filled rectangles
        for (let bitmap of bitmaps) {
            // Packing order: [MSB] [4 4] [3 4] ... [1 1] [0 1] ... [1 0] [0 0] [LSB]
            for (let offsetY = 0; offsetY < 5; offsetY++) {
                for (let offsetX = 0; offsetX < 5; offsetX++) {
                    if ((bitmap & 1) !== 0) {
                        mContext.fillRect(
                            x + offsetX * scale,
                            y + offsetY * scale,
                            rectSize, rectSize
                        );
                    }
                    bitmap >>= 1;
                }
            }
            x += stepX;
        }
    }

    function onAnimationFrame() {
        if (mStatus !== kStatus_Loading && mStatus !== kStatus_Running)
            return;

        if (mCanvas.clientWidth !== mViewWidth || mCanvas.clientHeight !== mViewHeight) {
            mViewWidth = mCanvas.width = mCanvas.clientWidth;
            mViewHeight = mCanvas.height = mCanvas.clientHeight;

            // Build a view matrix that preserves the game world's aspect ratio
            const viewAspect = mViewWidth / mViewHeight;
            if (viewAspect > kWorldAspect)
                mViewMatrix.a = mViewMatrix.d = mViewHeight / kWorldHeight;
            else
                mViewMatrix.a = mViewMatrix.d = mViewWidth / (kWorldHeight * kWorldAspect);
            mViewMatrix.e = mViewWidth / 2.0;
            mViewMatrix.f = mViewHeight / 2.0;

            // Build the game world's clipping path
            mViewClip = new Path2D();
            mViewClip.rect(-kWorldWidth / 2.0, -kWorldHeight / 2.0, kWorldWidth, kWorldHeight);
        }

        // Draw the interpolated game state
        interpolate();
        draw();

        if (mStatus === kStatus_Loading) {
            // Transition into running state when the first frame is visible
            mStatus = kStatus_Running;
            try {
                game.onRunning && game.onRunning();
            } catch {}
        }
        // Only continue to animate when the game is still running
        if (mStatus === kStatus_Running)
            requestAnimationFrame(onAnimationFrame);
    }

    function onKey(event, isDown) {
        // If the key is mapped to a button, update the input state
        const mask = kButtonMap[event.key];
        if (mask === undefined)
            return;
        if (isDown)
            mInputState |= mask;
        else
            mInputState &= ~mask;
    }
    const onKeyUp = event => onKey(event, false);
    const onKeyDown = event => onKey(event, true);

    function onSocketMessage(event) {
        const view = new DataView(event.data);
        const flags = view.getUint8(0);

        // Save the current state as the last state for interpolation
        mLastBallX = mNextBallX;
        mLastBallY = mNextBallY;
        mLastPaddleA = mNextPaddleA;
        mLastPaddleB = mNextPaddleB;
        mLastUpdateTime = mNextUpdateTime;
        mNextUpdateTime = performance.now();

        // Update all marked fields
        for (let offset = 1, bit = 0; bit < 8; bit++) {
            if ((flags & (1 << bit)) === 0)
                continue;
            switch (bit) {
                case 0: mPhase = view.getUint8(offset++); break;
                case 1:
                    mNextBallX = view.getFloat32(offset + 0, true);
                    mNextBallY = view.getFloat32(offset + 4, true);
                    offset += 8;
                    break;
                case 2: mScoreA = view.getUint8(offset++); break;
                case 3: mScoreB = view.getUint8(offset++); break;
                case 4:
                    mNextPaddleA = view.getFloat32(offset, true);
                    offset += 4;
                    break;
                case 5:
                    mNextPaddleB = view.getFloat32(offset, true);
                    offset += 4;
                    break;
            }
        }

        // If ball interpolation is disabled, set both positions to the same value
        if (flags & (1 << 6)) {
            mLastBallX = mNextBallX;
            mLastBallY = mNextBallY;
        }

        // Calculate the average update delta time
        if (mLastUpdateTime !== null && mNextUpdateTime !== null) {
            const updateDelta = mNextUpdateTime - mLastUpdateTime;
            if (mAverageUpdateDelta !== null)
                mAverageUpdateDelta = (mAverageUpdateDelta + updateDelta) / 2.0;
            else {
                mAverageUpdateDelta = updateDelta;
                // The game state is synchronized and can now be interpolated,
                // signal the ready callback
                if (mReadyCallback !== null) {
                    mReadyCallback();
                    mReadyCallback = null;
                }
            }
        }

        // If the input state changed since the last message, send an update
        if (mInputState !== mLastInputState) {
            mSocket.send(new Uint8Array([mInputState]));
            mLastInputState = mInputState;
        }

        // If the game was finished, clean up and transition into finished state
        if (mStatus === kStatus_Running && mPhase === kPhase_Finished) {
            try {
                mSocket.close();
            } catch {}
            removeEventListener('keyup', onKeyUp);
            removeEventListener('keydown', onKeyDown);

            mStatus = kStatus_Finished;
            try {
                game.onFinish && game.onFinish(mScoreA, mScoreB);
            } catch {}
        }
    }

    function onSocketClose() {
        if (mStatus !== kStatus_Loading && mStatus !== kStatus_Running)
            return;
        removeEventListener('keyup', onKeyUp);
        removeEventListener('keydown', onKeyDown);
        mStatus = kStatus_Error;
        try {
            game.onError && game.onError('Connection to server was lost');
        } catch {}
    }

    return game;
})();


// Set the functions called on game Events

Game.onLoading = drawLoadingScreen;
Game.onError = drawErrorScreen;