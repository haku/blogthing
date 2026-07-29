const versionBox = document.getElementById('version');
const statusBox = document.getElementById('status');

function setStatus(version, stts) {
  versionBox.textContent = version;
  statusBox.textContent = stts;
}

const msgpop = document.getElementById('msgpop')
let timerId = null

function setMsg(msg, fade=true) {
  if (timerId) clearTimeout(timerId)
  timerId = null

  msgpop.textContent = msg
  msgpop.classList.remove('fadeout')
  msgpop.style.visibility = 'visible'

  if (fade) timerId = setTimeout(() => msgpop.classList.add('fadeout'), 2000)
}

function setErr(msg) {
  setMsg(msg, false)
}

const infoBox = document.getElementById('info');
function setInfo(msg) {
  infoBox.textContent = msg;
}

export { setMsg, setErr, setStatus, setInfo }
