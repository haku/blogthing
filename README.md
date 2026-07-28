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
* [ ] way to mark ready to publish etc
* [ ] minimal file management for deleting uploads, re-inserting them, etc

bonus nice to have:

* [ ] dark theme
* [ ] nicer menus https://tiptap.dev/docs/editor/getting-started/style-editor/custom-menus
* [ ] store and show past versions
* [ ] actual auth (SSO) ooh so fancy
* [ ] https://tiptap.dev/docs/editor/extensions/functionality/focus
