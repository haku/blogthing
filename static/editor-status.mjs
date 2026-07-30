const versionBox = document.getElementById('version');
const statusBox = document.getElementById('state');

const States = {
  SAVED: Symbol.for("saved"),
  UNSAVED: Symbol.for("unsaved"),
  SAVING: Symbol.for("saving"),
  HISTORIC: Symbol.for("historic"),
}
const ALL_STATES = Object.entries(States).map(([k, v]) => Symbol.keyFor(v))

function setState(version, state) {
  versionBox.textContent = version;
  statusBox.classList.remove(...ALL_STATES)
  statusBox.classList.add(Symbol.keyFor(state))
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

export { setMsg, setErr, setState, States, setInfo }
