import { Editor } from 'https://esm.sh/@tiptap/core'
import StarterKit from 'https://esm.sh/@tiptap/starter-kit'
import FileHandler from 'https://esm.sh/@tiptap/extension-file-handler'
import Image from 'https://esm.sh/@tiptap/extension-image'

import * as Stts from './editor-status.mjs'

const editor = new Editor({
  element: document.querySelector('#editor'),
  extensions: [
    StarterKit.configure({
      link: {
        openOnClick: false,
        defaultProtocol: 'https',
      },
    }),
    FileHandler.configure({
      allowedMimeTypes: ['image/png', 'image/jpeg', 'image/gif', 'image/webp'],
      consumePasteEvent: true,
      onPaste: async (currentEditor, files, htmlContent) => {
        for (const file of files) {
          const formData = new FormData();
          formData.append('file', file);
          try {
            const resp = await fetch('/imgs', {
              method: 'POST',
              body: formData,
            });

            if (!resp.ok) {
              setErr(`Upload failed: ${resp}`)
              return
            }

            const { url } = await resp.json();
            currentEditor
              .chain()
              .insertContentAt(currentEditor.state.selection.anchor, {
                type: 'image',
                attrs: {
                  src: url,
                },
              })
              .focus()
              .run()
          }
          catch (err) {
            setErr(`Insert image failed: ${resp}`)
          }
        }
      },
    }),
    Image.configure({
      resize: {
        enabled: true,
        alwaysPreserveAspectRatio: true,
      },
    }),
  ],
})

// Wire up toolbar buttons
const buttons = document.querySelectorAll('[data-tiptap-button]')
buttons.forEach((button) => {
  button.addEventListener('click', () => {
    const command = button.dataset.tiptapButton

    switch (command) {
      case 'bold':
        editor.chain().focus().toggleBold().run()
        break
      case 'italic':
        editor.chain().focus().toggleItalic().run()
        break
      case 'strike':
        editor.chain().focus().toggleStrike().run()
        break
      case 'code':
        editor.chain().focus().toggleCode().run()
        break
      case 'h1':
        editor.chain().focus().toggleHeading({ level: 1 }).run()
        break
      case 'h2':
        editor.chain().focus().toggleHeading({ level: 2 }).run()
        break
      case 'bulletList':
        editor.chain().focus().toggleBulletList().run()
        break
      case 'orderedList':
        editor.chain().focus().toggleOrderedList().run()
        break
      case 'blockquote':
        editor.chain().focus().toggleBlockquote().run()
        break
      case 'codeBlock':
        editor.chain().focus().toggleCodeBlock().run()
        break
      case 'link':
        const prev = editor.getAttributes('link').href
        const url = prompt("URL:", prev)
        if (url) {
          if (prev) {
            editor.chain().focus().extendMarkRange('link').setLink({href: url}).run()
          }
          else {
            editor.chain().focus().setLink({href: url}).run()
          }
        }
        break
      case 'unlink':
        editor.chain().focus().unsetLink().run()
        break
    }

    updateActiveButtons()
  })
})

function updateActiveButtons() {
  const map = {
    bold: () => editor.isActive('bold'),
    italic: () => editor.isActive('italic'),
    strike: () => editor.isActive('strike'),
    code: () => editor.isActive('code'),
    h1: () => editor.isActive('heading', { level: 1 }),
    h2: () => editor.isActive('heading', { level: 2 }),
    bulletList: () => editor.isActive('bulletList'),
    orderedList: () => editor.isActive('orderedList'),
    blockquote: () => editor.isActive('blockquote'),
    codeBlock: () => editor.isActive('codeBlock'),
    link: () => editor.isActive('link'),
    unlink: () => editor.isActive('link'),
  }

  buttons.forEach((button) => {
    const command = button.dataset.tiptapButton
    const check = map[command]
    if (check && check()) {
      button.classList.add('is-active')
    } else {
      button.classList.remove('is-active')
    }
  })

  let info = null
  if (map.link()) {
    info = editor.getAttributes('link').href;
  }
  Stts.setInfo(info, true);
}

function extractTitle() {
  let title = null;
  editor.state.doc.descendants((node) => {
    if (title === null && node.type.name === "heading") {
      title = node.textContent.trim();
      return false;
    }
    return true;
  });
  return title;
}


// https://tiptap.dev/docs/editor/api/events
editor.on('selectionUpdate', updateActiveButtons)
editor.on('update', updateActiveButtons)

export { editor, extractTitle }
