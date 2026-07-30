# why do i think this is a good idea mrow

bare minimum bits needed to test if this is even possible and maybe worth the effort:

* [x] finish link handling
  * use prompt() see https://tiptap.dev/docs/editor/extensions/nodes/mathematics for example
* [x] image handling
  * https://tiptap.dev/docs/editor/extensions/functionality/filehandler
  * https://tiptap.dev/docs/editor/extensions/nodes/image
  * in DB
* [x] post title... just take first row of text?
* [x] process to converting JSON to HTML reliably with tiptapy
* [ ] serve the result

to make actually usable:

* [x] proper way to create new posts, list posts, etc
* [x] use postgres to store content
* [x] store and show past versions
* [x] editor view fits on screen nicely including mobile
* [x] some basic nav, like back to home from editor
* [x] way to mark ready to publish etc
* [ ] figure out what is going on with thing_date / sort-key / whatever
* [ ] minimal file management for deleting uploads, re-inserting them, etc

bonus nice to have:

* [x] move duplicated code to modules, bit of a tidy up
* [ ] dark theme
* [ ] fix my weird link popup with this? https://tiptap.dev/docs/editor/getting-started/style-editor/custom-menus
* [ ] how to clean up unused images?  how even to tell they are unused?  track when last fetched or something?
* [ ] once enough data, some DB indexes
* [ ] actual auth (SSO) ooh so fancy
* [ ] https://tiptap.dev/docs/editor/extensions/functionality/focus
* [ ] concurrent editing?
* [ ] gzip/etc save POSTS?  oh this is much more complex than i thought.
* [ ] save/restore cursor location?
* [ ] custom block for raw html?
* [ ] https://tiptap.dev/docs/editor/extensions/nodes/code-block-lowlight ?
* [ ] https://tiptap.dev/docs/editor/extensions/nodes/task-list ?
