# Discord Profile Studio

A CLI-driven Tkinter studio for designing Discord Rich Presence and profile widgets, with a live preview beside the
editor. Windows and Linux compatible.

## Roadmap

- [x] Lay out the package, CLI entry point, and packaging metadata.
- [ ] Define the presence, widget, account, and favourite data models.
- [ ] Resolve per-platform config, data, cache, and runtime paths.
- [ ] Read and write favourites to a versioned JSON store.
- [ ] Store tokens in the OS keyring with an encrypted local file as fallback.
- [ ] Add the OAuth2 sign-in flow and token refresh.
- [ ] Import existing CustomRP presets and settings into favourites.
- [ ] Connect to Discord over IPC and push a presence payload.
- [ ] Wire up the CLI commands for presence, widgets, favourites, and auth.
- [ ] Build the Tkinter window with the editor on the left and the preview on the right.
- [ ] Fill in the RPC section of the editor and its presence card in the preview.
- [ ] Fill in the widget section of the editor and its widget cards in the preview.
- [ ] Add a favourites list that previews an entry on hover and loads it on click.
- [ ] Cache and render asset images for the large and small icons.
- [ ] Put the app in the tray on both Windows and Linux with a close-to-tray option.
- [ ] Register autostart through the Windows run key and a Linux desktop entry.
- [ ] Guard against a second instance and hand off to the running one.
- [ ] Cover the models, storage, token store, and RPC layers with tests in CI.
- [ ] Publish the first release to PyPI.

## Tasks

MattFor

- [ ] Cli
- [x] Auth
- [x] Secrets
- [x] Secrets storage
- [ ] Widget section

Kamil

- [ ] Tray integration
- [ ] Tests
- [ ] Autostart integration
- [ ] Custom Rich Presence section
- [ ] Colour picker

Combined

- [ ] Favourites - I have no clue how to implement this yet

## License

MIT [LICENSE](LICENSE)

By [MattFor](https://github.com/MattFor), [KamilKlimas](https://github.com/KamilKlimas)
