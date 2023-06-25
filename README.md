# focus-time-app

A CLI tool for macOS and Windows that triggers your desktop OS's Focus Mode feature (and calls binary shell commands you
can specify), based on blocker events on your calendar.

For now, only Outlook 365 calendars are supported.

**Currently, it is not in a usable state yet!**

TODO create docs for other sections (Installation & Usage, Contributing, Roadmap)

## Out of scope

For the time being, the following features are not yet implemented (but PRs or issues are welcome):

- Supporting other calendar providers (Google Calendar, CalDAV)
- Syncing the state to other devices.
    - macOS/iOS supports this out-of-the-box. For Android devices, we would need to implement our own support, probably
      via a dedicated Android app, and a command for the desktop client to wake up the device (our app then checks the
      calendar). Wake up support can also be deferred, and our app could simply check for updated calendar events every
      X hours.
- GUI: could implement it as PySide6 GUI with a tray icon
- Linux support
- Analytics of focus time events

## Coding TODOs

- Test automated releases on both platforms
- Fix calendar helper for unit tests so that it uses its own credentials --> fixes manual E2E tests on macOS
- Automated dependency updates with Renovate Bot
- Version must be added to the code and the CLI's help text
- Implement other integration tests
- Once macOS 13 runners can handle AppleScript:
  - Prepare separate Outlook calendars for each OS, use them
  - Run CI tests on macOS

## Considerations for system level tests

- Cases:
  - sync: background job triggers on-off
    - configuration is run with enabled BG job
    - create an event 1 minute in the future, lasts 2 minutes
    - verify that DND is off
    - wait for 1 minute
    - verify that DND is on
    - wait for 2 minutes
    - verify that DND is off
  - start: TODO
  - stop: TODO
  - uninstall: TODO
