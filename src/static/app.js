const errorTimeouts = {};

function showError(element, message) {
    const elementId = element.id;
    
    if (errorTimeouts[elementId]) {
        clearTimeout(errorTimeouts[elementId]);
        delete errorTimeouts[elementId];
    }
    
    element.textContent = message;
    element.style.display = 'block'; 

    errorTimeouts[elementId] = setTimeout(() => {
        element.textContent = '';
        element.style.display = 'none';
        delete errorTimeouts[elementId];
    }, 7000);
}



async function clearMessages() {
    document.getElementById("message-box").innerHTML = "";
}

async function setMessagesHistory(messages) {
    messages.forEach(msg => {
        addMessage(msg)
    });
}


function addMessage(msg) {
    const messageBox = document.getElementById("message-box")
    
    // Check if user is already at the bottom (or very close to it)
    const isScrolledToBottom = messageBox.scrollHeight - messageBox.scrollTop - messageBox.clientHeight < 10;
    
    const time = msg.timestamp.slice(11, 16)
    
    let msgContent = msg.text
    if (msg.type == "system") {
        msgContent = `<div class="system"><i>${time}</i> <b>${msgContent}</b></div>`
    } else if (msg.type == "user") {
        msgContent = `<div class="user"><i>${time}</i> <b>${msg.sender}:</b> ${msgContent}</div>`
    }
    messageBox.innerHTML += msgContent
    
    if (isScrolledToBottom) {
        messageBox.scrollTop = messageBox.scrollHeight;
    }
}

let ws = null

async function sendMessage() {
    if (ws == null) {
      return;
    }
    const messageInput = document.getElementById("message-input")

    const message = messageInput.value
    if (message.length == 0) {
      return
    }
    messageInput.value = ""

    ws.send(JSON.stringify({ text: message }))
}

async function closeWebsocket() {
    if (ws) {
        ws.close()
        return true
    }
    return false
}


let isJoinedRoom = false
let joinedRoomId = null

function updateRoomInterface() {
  leaveBtn = document.getElementById("leave-room")
  sendBtn = document.getElementById("send-btn")

  if (leaveBtn && sendBtn) {
    if (isJoinedRoom) {
      leaveBtn.disabled = false;
      sendBtn.disabled = false;
    } else {
      leaveBtn.disabled = true;
      sendBtn.disabled = true;
    }
  }
}

function updateJoinedRoom(newValue) {

  if (isJoinedRoom == newValue) {
    return;
  }

  isJoinedRoom = newValue;
  updateRoomInterface();
}

async function establishWebsocketConnection(room_id, username) {
    joinedRoomId = room_id

    ws = new WebSocket(`/ws/messages/${room_id}/${username}`);
    const messageErrorBox = document.getElementById("message-error")

    ws.onopen = () => {
        console.log('WebSocket connection established');
      updateJoinedRoom(true)
    }

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.kind == "history") {
            setMessagesHistory(data.messages)
        } else if (data.kind == "message") {
            addMessage(data)
        } else if (data.kind == "error") {
            console.log("Websocket error received:", data.error_type, data.detail)
        }
    };
    
    ws.onerror = () => {
      showError(messageErrorBox, "WebSocket error occurred")
    }

    ws.onclose = () => {
      console.log('Disconnected');
        // Можно попробовать переподключиться
      updateJoinedRoom(false)
    };
}

async function createRoom() {
    const roomNameElement = document.getElementById("room-name");
    const roomName = roomNameElement.value
    const roomErrorBox = document.getElementById("room-error")  

    if (roomName.length == 0) {
      showError(roomErrorBox, "room name is empty")
      return
    }

    const usernameElement = document.getElementById("username");
    const username = usernameElement.value
    
    let response = null
    try {
      response = await fetch('/api/rooms', {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            room_name: roomName,
            username: username,
        })
      })
    } catch (e) {
      console.log("fetch error occurred ", e)
      showError(roomErrorBox, "connection error")
      return;
    }
    if (response.status > 299 || response.status < 200) {
        console.log("createRoom response status =", response.status)
        showError(roomErrorBox, "create room response ended with bad status")
        return
    }
    const data = await response.json()
    if (data.success) {
        await updateRooms()
        await joinRoom(data.room.id)
    } else {
      // console.log("createRoom response detail =", data.detail)
      showError(roomErrorBox, data.detail)
    }
    
} 

async function joinRoom(room_id) {
    if (joinedRoomId == room_id) {
      console.log("already joined this room.")
      return;
    }
    const usernameElement = document.getElementById("username");
    const username = usernameElement.value
    await leaveRoom()
    await establishWebsocketConnection(room_id, username);
}

async function leaveRoom() {
    const closed = await closeWebsocket()
    if (closed) {
      joinedRoomId = null
        clearMessages()
        return true
    }
    return false
}

async function updateRooms() {
    roomList = document.getElementById("room-list");
    if (roomList == null) {
        console.log("room list is null")
        return
    }
    let response = null
    try {
      response = await fetch('/api/rooms');
    } catch (e) {
      console.log("fetch error");
      return
    }
    if (response.status > 299 || response.status < 200) {
        console.log("updateRooms response status =", response.status)
        return
    }
    const data = await response.json();
    roomList.innerHTML = ""
    data["rooms"].forEach(room => {
        roomList.innerHTML += `\n<div class="room-item" onclick="joinRoom('${room.id}')">${room.creator}: ${room.name}</div>`;
    });
}

function setupEventListeners() {
    document.getElementById('message-input').addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault(); // чтобы не было переноса строки
            sendMessage();
        }
    });
  
    const leaveRoomBtn = document.getElementById('leave-room');
    if (leaveRoomBtn) {
      leaveRoomBtn.addEventListener('click', () => {
        leaveRoom();
      });
    } else {
      console.log("leave-room button not found")
    }
}

async function onLoaded() {
    setupEventListeners()
    await updateRooms();
  updateRoomInterface();
}



document.addEventListener("DOMContentLoaded", async () => {
    await onLoaded()
    setInterval(async () => {
        await updateRooms();
    }, 15000)
})
