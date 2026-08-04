# why do i think this is a good idea mrow

planned:

* [x] finish link handling
  * use prompt() see https://tiptap.dev/docs/editor/extensions/nodes/mathematics for example
* [x] image handling
  * https://tiptap.dev/docs/editor/extensions/functionality/filehandler
  * https://tiptap.dev/docs/editor/extensions/nodes/image
  * in DB
* [x] post title... just take first row of text?
* [x] process to converting JSON to HTML reliably with tiptapy
* [x] proper way to create new posts, list posts, etc
* [x] use postgres to store content
* [x] store and show past versions
* [x] editor view fits on screen nicely including mobile
* [x] some basic nav, like back to home from editor
* [x] way to mark ready to publish etc
* [x] way to organising things, maybe tags?
* [x] move duplicated code to modules, bit of a tidy up
* [x] dark theme
* [x] fix my weird link popup with this? https://tiptap.dev/docs/editor/getting-started/style-editor/custom-menus
* [ ] way to delete posts
* [ ] way to convert posts to serveable html
  * also see https://github.com/tugkanpilka/tiptap-python-utils
  * maybe ./blogthing-generate --tags "foo,bar" --output some/path/for/output/html
* [ ] figure out what is going on with thing_date / sort-key / whatever
* [ ] keyboard shortcuts
* [ ] image alt text
* [ ] minimal file management for deleting uploads, re-inserting them, etc
* [ ] how to clean up unused images?  how even to tell they are unused?
* [ ] actual auth (SSO) ooh so fancy
* [ ] once enough data, some DB indexes

maybe in the far future:

* [ ] custom block for raw html?
* [ ] favicon?  or any kinda logo
* [ ] concurrent editing?
* [ ] gzip/diff when send save POSTs?  oh this is much more complex than i thought.
* [ ] https://tiptap.dev/docs/editor/extensions/functionality/focus
* [ ] https://tiptap.dev/docs/editor/extensions/functionality/color ?
* [ ] https://tiptap.dev/docs/editor/extensions/nodes/code-block-lowlight ?
* [ ] https://tiptap.dev/docs/editor/extensions/nodes/task-list ?
