# Widget design

The design draws on Apple's [widgets](https://developer.apple.com/design/human-interface-guidelines/widgets), [sidebars](https://developer.apple.com/design/human-interface-guidelines/sidebars), [windows](https://developer.apple.com/design/human-interface-guidelines/windows), [buttons](https://developer.apple.com/design/human-interface-guidelines/buttons), and [typography](https://developer.apple.com/design/human-interface-guidelines/typography) guidance. This is an independent GTK/Xorg implementation, not Apple's WidgetKit or an Apple UI asset bundle.

- One primary task per card, with a clear title, main value, and secondary information.
- Shared corners and spacing; restrained colors distinguish content without competing with it.
- Separate light/dark colors and SVG variants. The appearance stylesheet is applied last so a light surface cannot override the dark palette.
- The renderer publishes actual logical dimensions every 120 ms. Fonts, images, rings, calendar cells and spacing respond to those dimensions. Compact cards reduce detail; larger ones expose more information.
- Scroll viewports prevent content's preferred size from preventing a smaller window. Overflow remains accessible without changing the saved card size.
- The library uses a native title bar, category sidebar, search and a stable detail pane. Decorations and repeated instructional copy have been reduced.

todomate uses the same native list, typography, theme and responsive shell as the other widgets. A single official WebKit session handles login; a local compatibility adapter uses the Firebase client loaded by that page to read today's own tasks and commit guarded completion transactions. No credentials leave the page. This is not a documented public todomate API. Obsidian notes are read from a selected local file and opened using the documented [Obsidian URI](https://help.obsidian.md/Extending+Obsidian/Obsidian+URI).

Glass and library previews share one tone mapping and palette. Small battery cards keep actual device icons and percentages rather than replacing Bluetooth devices with a hidden-device count. Overflow remains scrollable.

Stacks group equal-sized widgets without duplicating content. Only the active member is mapped; switching transfers its current placement and size. A committed body drag with at least 65% overlap joins equal-sized cards or merges existing stacks. The target outline does not affect layout. The pre-drag position is retained for a later split.

Two-finger horizontal scrolling is filtered before GTK dispatch only for an active stack. Gesture accumulation and a shared latch prevent repeated switching as the active window is replaced. Vertical events and unrelated input follow GTK's normal event path, so scrollable content and buttons retain their behavior. A small counter remains available for click/wheel navigation. Splitting restores original placements.

### Stable stack transitions (2.1.1)

`stack-switch` constructs the next scoped root before changing the current one, then hands the existing native window to that page. A clipped [GTK Stack](https://docs.gtk.org/gtk3/class.Stack.html) animates its content for 200 ms in the requested direction, honors GTK's animation setting, and releases outgoing widgets after transition completion. The X11 window remains mapped with the same ID, position and size. Its active instance name, scope, destroy handler and reload arguments move together. A failed destination build leaves the current host intact.

Cycling serializes callbacks and commits the geometry returned by the host. It does not restart the daemon, query desktop placement, snap again or close/open windows. Explicit size/placement changes in the library remain intentional geometry operations. The layout listener shares active dimensions with inactive members so a page does not start with an unrelated default layout.

Initial saved geometry is applied through GTK before first mapping. Native 180/500/900 ms restoration retries and the layout listener's 1.4 s correction were removed; these independent delayed moves could expose default geometry or race a user interaction. Frame-level regressions sample the full transition and the interval after those former delays, rather than waiting for the window to return to its final position.
