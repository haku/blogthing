const msgBox = document.getElementById('message');
const statusBox = document.getElementById('status');
const infoBox = document.getElementById('info');

function setMsg(msg) {
  msgBox.textContent = msg;
}

function setStatus(msg) {
  statusBox.textContent = msg;
}

function setInfo(msg) {
  infoBox.textContent = msg;
}

export { setMsg, setStatus, setInfo }
