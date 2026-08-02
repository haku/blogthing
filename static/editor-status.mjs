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

  if (msg) {
    msgBox.textContent = msg
    msgBox.classList.remove('fadeout')
    msgBox.style.visibility = 'visible'

    if (fade) timerId = setTimeout(() => msgBox.classList.add('fadeout'), 2000)
  }
  else {
    msgBox.style.visibility = 'hidden'
  }
}

function setErr(msg) {
  setMsg(msg, false)
}

export { setMsg, setErr, setState, States }
