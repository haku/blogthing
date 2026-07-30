import { editor, extractTitle } from './editor-tiptap.mjs'
import * as Misc from './misc.mjs'
import * as Stts from './editor-status.mjs'

const searchParams = new URLSearchParams(window.location.search);
function getParam(name, pattern) {
  const p = searchParams.get(name)
  if (p != null && !p.match(pattern)) {
    Stts.setErr(`Invalid ${name}.`)
    return null
  }
  return p
}

const LOAD_VERSION = getParam("version", /^[0-9]{1,10}$/)
const THING_ID     = getParam('thing_id', /^[0-9a-f]{1,10}$/)

const toolBox = document.getElementById('toolbox');
const publishedBtn = document.getElementById('thing_published');
const dateBox = document.getElementById('thing_date');

let thing_version = 0
let thing_published = false

function loadContent() {
  if (!THING_ID) {
    console.log("Skipping load as no thing_id.")
    return
  }

  const path = LOAD_VERSION == null
    ? `/things/${THING_ID}`
    : `/versions/${THING_ID}/${LOAD_VERSION}`

  if (LOAD_VERSION != null) {
    editor.setEditable(false, false)
    dateBox.disabled = true
    publishedBtn.disabled = true
  }

  return fetch(path)
    .then(async response => {
      await Misc.checkFetchResp(response)
      return response.json();
    })
    .then(data => {
      thing_version = data['thing_version']

      if (data['thing_published']) thing_published = data['thing_published']
      updatePublishedState()

      const date = data['thing_date'];
      if (date) dateBox.value = date;

      if (data.type)
        editor.chain().setContent(data).setTextSelection(0).focus().run()

      updatePageTitle()

      //Stts.setMsg(`Loaded v${thing_version}${LOAD_VERSION != null ? " (read-only)" : ""}.`)
    })
    .catch(error => {
      console.error('Error fetching thing:', error)
      Stts.setErr(`Error fetching thing: ${error}`)
    })
    .then(_ => {
      // runs even if load fails.
      startAutosaveLoop()
    })
}

function saveContent() {
  if (LOAD_VERSION != null) {
    console.log("Skipping save as load_version is set.")
    return
  }
  if (!THING_ID) {
    console.log("Skipping save as no thing_id.")
    return
  }

  const json = editor.getJSON();
  json['thing_version'] = thing_version + 1;
  json['thing_published'] = thing_published
  json['thing_date'] = dateBox.value;
  json['thing_title'] = updatePageTitle()

  return fetch(`/things/${THING_ID}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(json),
  })
  .then(async response => {
    await Misc.checkFetchResp(response)
    return response.json();
  })
  .then(data => {
    thing_version = data['thing_version'];
    //Stts.setMsg(`Saved v${thing_version}.`)
  })
}

function updatePageTitle() {
  const title = extractTitle()
  document.title = title != null ? `${title} - Blogthing` : "Blogthing"
  return title
}

function updatePublishedState() {
  publishedBtn.textContent = thing_published ? "Published" : "Unpublished"
  if (thing_published) {
    toolBox.classList.add('published')
  }
  else {
    toolBox.classList.remove('published')
  }
}

publishedBtn.addEventListener('click', () => {
  if (LOAD_VERSION != null) return

  const change_to = !thing_published
  if (confirm(`Set published=${change_to}?`)) {
    thing_published = change_to
    updatePublishedState()
    markDirty()
    // TODO trigger save now
  }
})


const SAVE_INTERVAL = 10000;
let dirty = false;
let saving = false;
let lastSave = 0;

function updateStatusBox() {
  const state = LOAD_VERSION ? Stts.States.HISTORIC
    : saving ? Stts.States.SAVING
    : dirty ? Stts.States.UNSAVED
    : Stts.States.SAVED
  Stts.setState(`v${thing_version}`, state)
}
function safeToExit() {
  return dirty === false && saving === false;
}
function markDirty() {
  if (lastSave === 0) lastSave = Date.now();
  dirty = true;
  updateStatusBox();
}
function markClean() {
  dirty = false;
  updateStatusBox();
}

async function autosaveLoop() {
  if (dirty && !saving && Date.now() - lastSave >= SAVE_INTERVAL) {
    await saveNow()
    // TODO backoff retry loop on errors?
  }
}

// returns true if it did something
async function saveIfNeeded() {
  if (!dirty) return false
  await saveNow()
  return true
}

async function saveNow() {
  if (saving) {
    console.log("Skipping save as save already in progress.")
    return
  }

  saving = true;
  markClean();

  try {
    await saveContent();
    lastSave = Date.now();
  }
  catch (error) {
    console.error('Error saving thing:', error)
    markDirty();
    Stts.setErr(`Error saving thing: ${error}`)
  }
  finally {
    saving = false;
    updateStatusBox();
  }
}

function startAutosaveLoop() {
  if (LOAD_VERSION != null) {
    console.log("Not starting autosave as load_version is set.")
    updateStatusBox()
    return
  }

  markClean()
  setInterval(autosaveLoop, 1000);

  editor.on('update', markDirty)
  dateBox.addEventListener('input', markDirty)

  window.addEventListener('beforeunload', (event) => {
    if (!safeToExit()) event.returnValue = "Discard unsaved changes?";
  });
}

function start() {
  editor.on('create', loadContent)
}


export { THING_ID, LOAD_VERSION, start, saveIfNeeded }
