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

## TODOs

- Logging system
- CD pipeline that creates automated builds for Windows and macOS
- Testing
    - To build a system-level test (that tests the frozen binaries), we would need a --non-interactive flag for the
      ConfigurationCommand
    - We can mock e.g. a calendar provider to test the sync command (module-level test)
- CI pipeline that runs tests
- Automated dependency updates with Renovate Bot (once tests exist)
