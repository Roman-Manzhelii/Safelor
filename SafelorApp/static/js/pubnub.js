let pubnub

let zone_status_map
async function setupPubNub() {
  async function refreshToken() {
    try {
      const newToken = await requestToken();
      let parsedToken = pubnub.parseToken(newToken)
      console.log("Refreshed token:", newToken);
      pubnub.setAuthKey(newToken); 
      const refreshInterval = (parsedToken['ttl']*60*1000)-(30*1000);
      setTimeout(refreshToken, refreshInterval);
    } catch (err) {
      console.error("Error refreshing token:", err);
    }
  }
  const token = await requestToken();
  const cipherKey = await requestCipher();
  console.log("Cipher key in js",cipherKey)
  pubnub = new PubNub({
    subscribeKey: "sub-c-addb02ed-900a-48f7-9825-f3f66fc48dab",
    userId: "safelor_client",
    authKey: token,
    cipherKey: cipherKey
  });
  const channel = pubnub.channel("ppe_violation");
  const channel2 = pubnub.channel("return_online_status");
  const scan_data_subscription = channel.subscription();
  const online_status_subscription = channel2.subscription();

  scan_data_subscription.addListener({
    status: (s) => {
      console.log("Status", s.category);
    },
    message: (m) => {
      console.log("Received message", m);
      console.log("Message channel", m.channel);
      if (m.channel === "ppe_violation") {
        console.log("matched channel");
        console.log(m.message)
        handleScanViolation(m.message);
        getNotifications();
      }
    },
  });
  online_status_subscription.addListener({
    status: (s) => {
      console.log("Status", s.category);
    },
    message: (m) => {
      console.log("Received message", m);
      console.log("Message channel", m.channel);
      if (m.channel === "return_online_status") {
        console.log("matched channel");
        console.log(m.message)
        zone_status_map = m.message.zone_status_map
        console.log("setting zone status colors")
        setZoneStatusColors()
      }
    },
  });
  scan_data_subscription.subscribe();
  online_status_subscription.subscribe();
  console.log("PubNub SET UP");
  let parsedToken = pubnub.parseToken(token)
  console.log("Parsed token = ",parsedToken)
  const refreshInterval = (parsedToken['ttl'] * 60 * 1000) - (30 * 1000); 
  setTimeout(refreshToken, refreshInterval);
}

async function requestToken(channel) {
  try {
    const response = await fetch("/get_pubnub_token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ channel }),
    });
    const data = await response.json();
    if (data.token) {
      return data.token;
    } else {
      console.log("Failed to retrieve token");
      return null;
    }
  } catch (error) {
    console.error("Error fetching token ", error);
    return null;
  }
}

async function requestCipher() {
  try {
    const response = await fetch("/get_cipher_key", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    const data = await response.json();
    if (data.cipher_key) {
      return data.cipher_key;
    } else {
      console.log("Failed to retrieve cipher_key");
      return null;
    }
  } catch (error) {
    console.error("Error fetching cipher key ", error);
    return null;
  }
  
}



async function getNotifications() {
  try {
    const response = await fetch("/get_notifications", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    const data = await response.json();
    const notificationContainer = document.getElementById(
      "id_dropdown_notifications_container"
    );

    const onOff = document.getElementById(
      "no_notific_found_container"
    );

    const noNotifBell = document.getElementById(
      "bell_always"
    );

    const notifBell = document.getElementById(
      "bell_always_two"
    );
    console.log("length:  ", data.notifications.length)

    if (data.notifications.length > 0) {



      onOff.style.display = "none"; 
      noNotifBell.style.display = "none"; 
      notifBell.style.display = "block";
      data.notifications.forEach(notification => {
        addNotificationToList(notificationContainer, notification);
      });
      console.log("Received notifications in getNotifications", data.notifications);
    } else {
      notifBell.style.display = "none"; 
      noNotifBell.style.display = "block";
      onOff.style.display = "block"; 
      console.log("No notifications found");
    }
  } catch (error) {
    console.error("Error fetching notifications ", error);
    return null;
  }
}

function handleScanViolation(message) {
  console.log("Handling violation", message);
  const notificationContainer = document.getElementById(
    "notification-container"
  );
  const notificationListContainer = document.getElementById(
    "id_dropdown_notifications_container"
  );

  const notificationElement = document.createElement("div");
  notificationElement.className = "pubnub_notification_in_cont";
  console.log("scan object ",message)
  notificationElement.innerHTML = `
    <p class="drop_notif_time">${message.data_time}</p>
    <a href="/ppe_scan?scan_id=${message.scan_id}">
      <button class="drop_notif_btn">Take me there</button>
    </a>
  `;
  // notificationListContainer.prepend(notificationElement);
  
  const notification = document.createElement("div");
    notification.innerHTML = `<strong>Notification:</strong> ${message.scan_id}
      <button class="notification_btn">Take me there</button>
      `;
  notification.innerHTML = `
  <form action="/ppe_scan?scan_id=${ message.scan_id }" method="POST">
  <div>
    <i class="fa-solid fa-triangle-exclamation fa-shake" style="font-size: 1.5em;"></i>
  </div>
  <div style="margin-left: 5vh;">
  <strong style="font-variant: small-caps;">Invalid ppe detected!</strong>
    <button type="submit" class="notification_btn">Take me there</button>
    </div>
    </form>
    `;

  notification.className = "pubnub_notification";

  notificationContainer.appendChild(notification);
  setTimeout(() => notificationContainer.removeChild(notification), 10000);
}

function addNotificationToList(notificationListContainer,scan_data){
  const notificationElement = document.createElement("div");
  notificationElement.className = "pubnub_notification_in_cont";
  notificationElement.innerHTML = `
    <p class="drop_notif_time">${scan_data.data_time}</p>
    <form action="/ppe_scan?scan_id=${ scan_data._id }" method="POST">
      <button type="submit" class="drop_notif_btn">Take me there</button>
      </form>
    </a>
  `;
  notificationListContainer.prepend(notificationElement);
}

function triggerScanChecked(scanId) {
  try{
    const url = `/check_scan?scan_id=${scanId}`;
    fetch(url, {
        method: 'POST', 
        headers: {
            'Content-Type': 'application/json',
        },
    })
  } catch (error) {
    console.error("Error posting scan id to be checked ", error);
  }
}

function setZoneStatusColors() {
  console.log("Setting online colors")
  for (const key in zone_status_map) {
    if (zone_status_map.hasOwnProperty(key)) {
      let statusElement = document.getElementById("online_status_"+key);
      if (statusElement) {
        console.log("Element exists")
        if (zone_status_map[key]) {
          console.log("Setting color green for ",key)
          statusElement.style.backgroundColor = "green";
        } else {
          console.log("Setting color red for ",key)
          statusElement.style.backgroundColor = "red";
        }
    }
    else {
      console.log("Element does not exist")
    }
  }
}
}


async function requestZoneStatus() {
  try {
    const response = await fetch("/zone_status_request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    const data = await response.json();
    console.log("DATA RETURNED in request zone status",data)
    if (data.zone_status_map) {
      console.log("REQUEST ZONE STATUS ",data.zone_status_map)
      zone_status_map = data.zone_status_map
      setZoneStatusColors()
    } else {
      console.log("Failed to get zone_status");
      return null;
    }
  } catch (error) {
    console.error("Error fetching zone_status ", error);
    return null;
  }
}


window.addEventListener("load", () => {
  requestZoneStatus();
  setupPubNub();
  getNotifications();
});

