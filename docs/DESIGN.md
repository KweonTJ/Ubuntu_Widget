# Design in 2.0

The design draws on Apple's [widgets](https://developer.apple.com/design/human-interface-guidelines/widgets), [sidebars](https://developer.apple.com/design/human-interface-guidelines/sidebars), [windows](https://developer.apple.com/design/human-interface-guidelines/windows), [buttons](https://developer.apple.com/design/human-interface-guidelines/buttons), and [typography](https://developer.apple.com/design/human-interface-guidelines/typography) guidance. This is an independent GTK/Xorg implementation, not Apple's WidgetKit or an Apple UI asset bundle.

- One primary task per card, with a clear title, main value, and secondary information.
- Shared corners and spacing; restrained colors distinguish content without competing with it.
- Separate light/dark colors and SVG variants. The appearance stylesheet is applied last so a light surface cannot override the dark palette.
- The renderer publishes actual logical dimensions every 120 ms. Fonts, images, rings, calendar cells and spacing respond to those dimensions. Compact cards reduce detail; larger ones expose more information.
- Scroll viewports prevent content's preferred size from preventing a smaller window. Overflow remains accessible without changing the saved card size.
- The library uses a native title bar, category sidebar, search and a stable detail pane. Decorations and repeated instructional copy have been reduced.

todomate uses the same native list, typography, theme and responsive shell as the other widgets. A single official WebKit session handles login; a local compatibility adapter uses the Firebase client loaded by that page to read today's own tasks and commit guarded completion transactions. No credentials leave the page. This is not a documented public todomate API. Obsidian notes are read from a selected local file and opened using the documented [Obsidian URI](https://help.obsidian.md/Extending+Obsidian/Obsidian+URI).

Glass and library previews share one tone mapping and palette. Small battery cards keep actual device icons and percentages rather than replacing Bluetooth devices with a hidden-device count. Overflow remains scrollable.

Stacks group equal-sized widgets without duplicating content. Only the active member is mapped; switching transfers its current placement and size. A small counter provides click/wheel navigation. Splitting restores the original placements.
