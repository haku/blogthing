const versionBox = document.getElementById('version');
const statusBox = document.getElementById('status');

function setStatus(version, stts) {
  versionBox.textContent = version;
  statusBox.textContent = stts;
}

const msgBox = document.getElementById('pop-msg')
let timerId = null

function setMsg(msg, fade=true) {
  if (timerId) clearTimeout(timerId)
  timerId = null

  msgBox.textContent = msg
  msgBox.classList.remove('fadeout')
  msgBox.style.visibility = 'visible'

  if (fade) timerId = setTimeout(() => msgBox.classList.add('fadeout'), 2000)
}

function setErr(msg) {
  setMsg(msg, false)
}

const infoBox = document.getElementById('pop-info');
function setInfo(msg, link=false) {
  if (msg) {
    if (link) {
      infoBox.innerHTML = `<a href=${msg}>${msg}</a>`
    }
    else {
      infoBox.textContent = msg
    }
    infoBox.style.visibility = 'visible'
  }
  else {
    infoBox.style.visibility = 'hidden'
  }
}

export { setMsg, setErr, setStatus, setInfo }
