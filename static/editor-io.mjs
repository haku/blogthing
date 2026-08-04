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
const tagsBox = document.getElementById('thing_tags');
const addTagBtn = document.getElementById('addtag');
const dateBox = document.getElementById('thing_date');
const publishedBtn = document.getElementById('thing_published');

let autosave_interval_id = null
let thing_version = 0
let thing_tags = []
let thing_published = false

function setReadOnly() {
  editor.setEditable(false, false)
  addTagBtn.disabled = true
  dateBox.disabled = true
  publishedBtn.disabled = true

  if (autosave_interval_id != null) {
    clearInterval(autosave_interval_id)
    autosave_interval_id = null
  }
}

function lockForVersionConflict() {
  setReadOnly()
  Stts.setErr("Changes can not be saved because they conflict with changes made in another session."
    + "  Reload required, which will discard changes since last save.")
}

function loadContent() {
  if (!THING_ID) {
    console.log("Skipping load as no thing_id.")
    return
  }

  const path = LOAD_VERSION == null
    ? `/api/things/${THING_ID}`
    : `/api/versions/${THING_ID}/${LOAD_VERSION}`

  if (LOAD_VERSION != null) {
    setReadOnly()
  }

  return fetch(path)
    .then(async response => {
      await Misc.checkFetchResp(response)
      return response.json();
    })
    .then(data => {
      if (!areChangesSaved()) {
        lockForVersionConflict()
        return
      }

      thing_version = data['thing_version']

      if (data['thing_tags']) thing_tags = data['thing_tags']
      updateTags()

      if (data['thing_published']) thing_published = data['thing_published']
      updatePublishedState()

      const date = data['thing_date'];
      if (date) dateBox.value = date;

      if (data.type)
        editor.chain().setContent(data).setTextSelection(0).focus().run()

      markClean()
      updatePageTitle()
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
  json['thing_tags'] = thing_tags
  json['thing_published'] = thing_published
  json['thing_date'] = dateBox.value;
  json['thing_title'] = updatePageTitle()

  return fetch(`/api/things/${THING_ID}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(json),
  })
  .then(async response => {
    if (response.status == 409) {
      lockForVersionConflict()
      return false
    }
    await Misc.checkFetchResp(response)

    const parsed = await response.json();
    thing_version = parsed['thing_version'];
    Stts.setErr(null)

    return true
  })
}

function updatePageTitle() {
  const title = extractTitle()
  document.title = title != null ? `${title} - Blogthing` : "Blogthing"
  return title
}

function updateTags() {
  if (thing_tags.length > 0) {
    tagsBox.innerHTML = ""
    const tmpl = document.getElementById('tagtemplate');
    for (let tag of thing_tags) {
      const e = tmpl.content.cloneNode(true)
      const btn = e.querySelector("button")
      btn.textContent = tag
      if (LOAD_VERSION == null) {
        btn.addEventListener('click', () => promptRemoveTag(tag))
      }
      else {
        btn.disabled = true
      }
      tagsBox.append(e)
    }
  }
  else {
    tagsBox.textContent = "(none)"
  }
}

function promptRemoveTag(tag) {
  if (confirm(`Remove tag?: ${tag}`)) {
    const len = thing_tags.length
    thing_tags = thing_tags.filter(t => t !== tag)
    if (thing_tags.length != len) {
      updateTags()
      markDirty()
    }
  }
}

addTagBtn.addEventListener('click', () => {
  let tag
  while(tag = prompt("Tag: (max 50 characters)", tag)) {
    if (tag.length < 50) {
      if (!thing_tags.includes(tag)) {
        thing_tags.push(tag)
        updateTags()
        markDirty()
      }
      break
    }
  }
})

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
function areChangesSaved() {
  return dirty === false && saving === false;
}
function markDirty() {
  if (lastSave === 0) lastSave = Date.now();
  dirty = true;
  updateStatusBox();
}
function markClean() {
  dirty = false;
  lastSave = Date.now();
  updateStatusBox();
}

async function autosaveLoop() {
  if (!saving && Date.now() - lastSave >= SAVE_INTERVAL) {
    if (dirty) {
      await saveNow()
      // TODO backoff retry loop on errors?
    }
    else {
      lastSave = Date.now()
      checkForRemoteChanges()
    }
  }
}

// returns true if it tried to do something
async function saveIfNeeded() {
  if (!dirty) return false
  await saveNow()
  return true
}

// returns true if successful
async function saveNow() {
  if (saving) {
    console.log("Skipping save as save already in progress.")
    return
  }

  saving = true;
  updateStatusBox();

  try {
    if (!await saveContent()) return false
    markClean()
    return true
  }
  catch (error) {
    console.error('Error saving thing:', error)
    Stts.setErr(`Error saving thing: ${error}`)
    return false
  }
  finally {
    saving = false;
    updateStatusBox();
  }
}

function checkForRemoteChanges() {
  fetch(`/api/things/${THING_ID}/version`)
    .then(async response => {
      await Misc.checkFetchResp(response)
      return response.json();
    })
    .then(data => {
      if (thing_version === data['thing_version']) return;
      if (areChangesSaved()) {
        loadContent().then(() => {
          Stts.setMsg(`Loaded version ${thing_version}`)
        })
      }
      else {
        lockForVersionConflict()
      }
    })
}

function startAutosaveLoop() {
  if (autosave_interval_id != null) {
    console.log("Not starting autosave as it is already started.")
    return
  }

  if (LOAD_VERSION != null) {
    console.log("Not starting autosave as load_version is set.")
    updateStatusBox()
    return
  }

  autosave_interval_id = setInterval(autosaveLoop, 1000);

  editor.on('update', markDirty)
  dateBox.addEventListener('input', markDirty)

  window.addEventListener('beforeunload', (event) => {
    if (!areChangesSaved()) event.returnValue = "Discard unsaved changes?";
  });
}

function start() {
  editor.on('create', loadContent)
}


export { THING_ID, LOAD_VERSION, start, saveIfNeeded }
