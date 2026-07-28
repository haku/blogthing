# why do i think this is a good idea mrow

bare minimum bits needed to test if this is even possible and maybe worth the effort:

* [ ] finish link handling
  * use prompt() see https://tiptap.dev/docs/editor/extensions/nodes/mathematics for example
* [x] image handling
  * https://tiptap.dev/docs/editor/extensions/functionality/filehandler
  * https://tiptap.dev/docs/editor/extensions/nodes/image
* [x] post title... just take first row of text?
* [ ] process to converting JSON to HTML reliably with tiptapy
* [ ] serve the result

to make actually usable:

* [ ] proper way to create new posts, list posts, etc
* [ ] way to mark ready to publish etc
* [ ] use postgres to store content
* [ ] minimal file management for deleting uploads, re-inserting them, etc

bonus nice to have:

* [ ] dark theme
* [ ] nicer menus https://tiptap.dev/docs/editor/getting-started/style-editor/custom-menus
* [ ] way to see past versions
* [ ] actual auth (SSO) ooh so fancy
* [ ] https://tiptap.dev/docs/editor/extensions/functionality/focus
