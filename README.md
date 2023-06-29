# focus-time-app

A CLI tool for macOS and Windows that triggers your desktop OS's Focus Mode feature (and calls binary shell commands you
can specify), based on blocker events on your calendar.

For now, only Outlook 365 calendars are supported.

**Currently, it is not in a usable state yet!**

TODO create docs for other sections (Installation & Usage, Contributing, Roadmap)

Running on macOS:
- Unpack, then double click the focus-time binary, it will fail, macOS will show a message such as 
- "“focus-time” cannot be opened because it is from an unidentified developer." or "“focus-time” can’t be opened because Apple cannot check it for malicious software." if you run it from the Terminal
- On macOS 12, go to System settings -> Security control pane -> General tab.
- On macOS 13, go to System settings -> Privacy & Security
- Look for a message such as "focus-time" was blocked from use because it is not from an identified developer
- CLick the "Allow anyway" button
- Now run it from the Terminal, there will still be a pop-up, but it has an Open button
- Another error message might appear that warns you about Python being from an unidentified developer. Go to system settings again and allow it

It's probably easier to just have people build the app themselves, and exclude the macOS zip from the release

For future reference:
https://federicoterzi.com/blog/automatic-code-signing-and-notarization-for-macos-apps-using-github-actions/

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
