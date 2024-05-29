$(document).ready(function() {
  let socket;
  let username; // Store username after successful registration

  // Function to initialize WebSocket connection
  function initializeWebSocket() {
    socket = new WebSocket('ws://localhost:8000/message');

    // WebSocket event handlers
    socket.onopen = function (event) {
      console.log('WebSocket connection established.');
    };

    socket.onmessage = function (event) {
      const data = JSON.parse(event.data);
      const sender = data.username;
      const message = data.message;
      const messageClass = data.isMe ? 'user-message' : 'other-message';

      const messageElement = $('<li>').addClass('clearfix');
      const messageBody = $('<div>').addClass('message-body').text(message);
      const messageSender = $('<span>').addClass('message-sender').text(sender);

      messageElement.addClass(messageClass);
      messageElement.append(messageBody);

      if (data.isMe) {
        messageElement.addClass('user-message');
        messageElement.append($('<span>').addClass('float-right').append(messageSender));
      } else {
        messageElement.addClass('other-message');
        messageElement.append(messageSender);
      }

      $('#messages').append(messageElement);
      $('#chat').scrollTop($('#chat')[0].scrollHeight);
    };

    socket.onerror = function (event) {
      console.error('WebSocket error. Please rejoin the chat.');
      showJoinModal();
    };

    socket.onclose = function (event) {
      if (event.code === 1000) {
        console.log('WebSocket closed normally.');
      } else {
        console.error('WebSocket closed with error code: ' + event.code + '. Please rejoin the chat.');
        showJoinModal();
      }
    };
  }

  // Function to show the registration modal
  function showJoinModal() {
    $('#usernamePasswordModal').modal('show');
  }

  // Event listener for "Join" button click
  $('#open-modal').click(function () {
    showJoinModal();
  });

  // Function to handle registration and join chat
  async function joinChat(username, password) {
    try {
      const response = await $.ajax({
        type: "POST",
        url: "/register",
        data: JSON.stringify({ username, password }),
        contentType: "application/json"
      });

      console.log('User registered successfully');
      username = response.username || username; // Store username for messages
      initializeWebSocket();
      $('#usernamePasswordModal').modal('hide');
      $('#chat').show();
      $('#message-input').show();
    } catch (error) {
      console.error('Error registering user:', error);
      alert('Error registering user: ' + error.message);
    }
  }

  // Event listener for "Register" button click
  $('#register').click(function () {
    const username = $('#usernameInput').val();
    const password = $('#passwordInput').val();
    if (username && password) {
      joinChat(username, password);
    } else {
      alert('Please enter both username and password.');
    }
  });

  // Event listener for "Send" button click
  $('#send').click(function () {
    const message = $('#message').val();
    if (message) {
      socket.send(JSON.stringify({ message, username })); // Include username
      $('#message').val('');
    }
  });

  // Event listener for Enter key press in message input
  $('#message').keydown(function (event) {
    if (event.key === "Enter") {
      sendMessage(); // Removed redundancy, function call already in send button click
    }
  });
});
