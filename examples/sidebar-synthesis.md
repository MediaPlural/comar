# synthesize: sidebar  [navigation]
Persistent side panel with primary navigation sections/folders.
aliases: drawer, navigation rail, nav rail, hamburger, left sidebar, side panel, LeftSidebarView, LeftSidebarFolderView, SidebarCapView

## Walkthrough directives (copy-from, 4)
  - **Telegram**: Pressing the top-left control opens a menu drawer from within a chat session.
  - **Telegram**: Drawer contents: Hermes-style sidebar with session management plus a pinned chats/sessions area.
  - **Telegram**: Build the left-hand control/navigation rail (like the Foxy prototype) as the app's primary navigation area.
  - **ChatGPT**: Include a Pinned section in the sidebar drawer for pinned sessions, plus a dedicated notebook/saved-notes area.

## Cross-app comparison (6 apps)
  app                aspects                                      clean members
  ------------------ -------------------------------------------- ------------------------------
  1Password          container, item, folder, icon                10
  Cursor             toggle, position, container, move            10
  Obsidian           toggle, position, move, pin, empty           9
  Snagit             toggle, container, position, item, background, divider, constraint, state, menu 10
  Telegram           toggle, position, container, item, folder, header 7
  Visual Studio Code toggle, icon, secondary                      10

## Shared pattern — what every app converges on (>=2 apps)
  1. **toggle** (5 apps)
       Cursor: openAndCloseSidebar, toggleSidebarP
       Obsidian: sidebar-close, sidebar-open
       Snagit: enableToggleSidebarMenuItem, hideSidebarView
       Telegram: sidebarShown
       Visual Studio Code: agentSecondarySidebarToggleClosedIcon, agentSidebarToggleClosedIcon, agentSidebarToggleOpe, agentSidebarToggleOpenIcon, nch.action.chat.openNewSessionSidebar.copilot-cloud-agent
  2. **position** (4 apps)
       Cursor: miMoveSidebarLeft, miMoveSidebarRight, moveSidebarLeft, moveSidebarRight
       Obsidian: sidebar-left, sidebar-right
       Snagit: sidebarViewTrailingConstraint, leadingSidebarViews
       Telegram: leftSidebarController, LeftSidebarArguments, LeftSidebarFolderView, LeftSidebarFolderItem, LeftSidebarView
  3. **container** (4 apps)
       1Password: iconContainer VaultSidebar, sidebar DialogPanes
       Cursor: moveFocusedView.newContainerInSidebar, sidebarContainer
       Snagit: sidebarContainerView, sidebarViewTrailingConstraint, hideSidebarView, leadingSidebarViews
       Telegram: LeftSidebarFolderView, LeftSidebarView, SidebarCapView
  4. **item** (3 apps)
       1Password: listItem VaultSidebar
       Snagit: enableToggleSidebarMenuItem
       Telegram: LeftSidebarFolderItem
  5. **folder** (2 apps)
       1Password: iconContainer VaultSidebar, listItem VaultSidebar, plusIcon VaultSidebar
       Telegram: LeftSidebarFolderView, LeftSidebarFolderItem
  6. **icon** (2 apps)
       1Password: iconContainer VaultSidebar, plusIcon VaultSidebar
       Visual Studio Code: agentSecondarySidebarToggleClosedIcon, agentSidebarToggleClosedIcon, agentSidebarToggleOpenIcon
  7. **move** (2 apps)
       Cursor: miMoveSidebarLeft, miMoveSidebarRight, moveFocusedView.newContainerInSidebar, moveSidebarLeft, moveSidebarRight
       Obsidian: optionSlidingSidebar, optionSlidingSidebarDesc

## Divergences — single-app specifics (build only if you need them)
  - **state** (Snagit): currentSidebarState, kEditorSidebarStateKey, restoreSidebarForNarration
  - **secondary** (Visual Studio Code): agentSecondarySidebar, agentSecondarySidebarToggleClosedIcon
  - **header** (Telegram): SidebarCapView
  - **background** (Snagit): sidebarBackground
  - **divider** (Snagit): sidebarDivider
  - **constraint** (Snagit): sidebarViewTrailingConstraint
  - **menu** (Snagit): enableToggleSidebarMenuItem
  - **pin** (Obsidian): canPinSidebar
  - **empty** (Obsidian): emptySidebar

## Ranked build recommendations
  1. **toggle** — copy from **Telegram**  (5 apps)
       directive-backed; evidence: sidebarShown
  2. **position** — copy from **Telegram**  (4 apps)
       directive-backed; evidence: leftSidebarController, LeftSidebarArguments, LeftSidebarFolderView
  3. **container** — copy from **Telegram**  (4 apps)
       directive-backed; evidence: LeftSidebarFolderView, LeftSidebarView, SidebarCapView
  4. **item** — copy from **Telegram**  (3 apps)
       directive-backed; evidence: LeftSidebarFolderItem
  5. **folder** — copy from **Telegram**  (2 apps)
       directive-backed; evidence: LeftSidebarFolderView, LeftSidebarFolderItem
  6. **icon** — copy from **Visual Studio Code**  (2 apps)
       densest evidence (3 symbols); e.g. agentSecondarySidebarToggleClosedIcon, agentSidebarToggleClosedIcon, agentSidebarToggleOpenIcon
  7. **move** — copy from **Cursor**  (2 apps)
       densest evidence (5 symbols); e.g. miMoveSidebarLeft, miMoveSidebarRight, moveFocusedView.newContainerInSidebar
  8. **header** — copy from **Telegram**  (1 app)
       directive-backed; evidence: SidebarCapView
  9. **background** — copy from **Snagit**  (1 app)
       densest evidence (1 symbols); e.g. sidebarBackground
  10. **divider** — copy from **Snagit**  (1 app)
       densest evidence (1 symbols); e.g. sidebarDivider
  11. **constraint** — copy from **Snagit**  (1 app)
       densest evidence (1 symbols); e.g. sidebarViewTrailingConstraint
  12. **state** — copy from **Snagit**  (1 app)
       densest evidence (3 symbols); e.g. currentSidebarState, kEditorSidebarStateKey, restoreSidebarForNarration
  13. **menu** — copy from **Snagit**  (1 app)
       densest evidence (1 symbols); e.g. enableToggleSidebarMenuItem
  14. **pin** — copy from **Obsidian**  (1 app)
       densest evidence (1 symbols); e.g. canPinSidebar
  15. **empty** — copy from **Obsidian**  (1 app)
       densest evidence (1 symbols); e.g. emptySidebar
  16. **secondary** — copy from **Visual Studio Code**  (1 app)
       densest evidence (2 symbols); e.g. agentSecondarySidebar, agentSecondarySidebarToggleClosedIcon

## Build it this way (extracted design pattern)
  Every app implements `sidebar` as the same core: toggle, position, container, item. That shared shape is the part you must build first; the variations (background, constraint, divider, empty, header, menu, pin, secondary, state) are optional, adopt only if your surface needs them. Primary copy source: Telegram (directive of record).

