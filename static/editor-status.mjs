const versionBox = document.getElementById('version');
const statusBox = document.getElementById('status');

function setStatus(version, stts) {
  versionBox.textContent = version;
  statusBox.textContent = stts;
}

const msgBox = document.getElementById('message');
const infoBox = document.getElementById('info');

function setMsg(msg) {
  msgBox.textContent = msg;
}

function setInfo(msg) {
  infoBox.textContent = msg;
}

export { setMsg, setStatus, setInfo }
