
const warningBt1n = document.getElementById("btn_warning_clicking");
warningBt1n.onclick =sendWarningEmpPage

function sendWarningEmpPage() {
  console.log('warning sent')
  const notification = document.createElement("div");

  notification.innerHTML = `<strong>Warning has been sent:</strong> 
    `;
  notification.innerHTML = `
    <div>
      <i class="fa-solid fa-triangle-exclamation fa-shake" style="font-size: 1.5em;"></i>
    </div>
      `;

  notificationContainer.appendChild(notification);
  setTimeout(() => notificationContainer.removeChild(notification), 10000);
}

