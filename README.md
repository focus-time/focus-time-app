# focus-time-app

The **Focus time app** is a _CLI_ tool for macOS and Windows that regularly checks your calendar for "focus time"
blocker events. Whenever such events begin or end, it triggers your desktop OS's Focus Mode feature, or calls
shell commands that you can configure.

It saves you from having to _manually_ start or stop your operating system's "Do not Disturb" (focus mode/assist) mode,
close/open programs, etc., whenever a focus
time period begins or ends.

For now, **only Outlook 365 and CalDAV calendars are supported**. CalDAV support is in an early stage and may still
have several problems, depending on the calendar provider/server.

## Features

- Easy to set up: there is a dedicated configuration command that interactively queries all necessary information
- Various configuration settings, such as:
    - The title/subject of the focus time blocker events
    - The reminder (_off_, or _on_ and the number of minutes) of the focus time blocker events. This also overwrites
      the reminder of _existing_ events, which is useful if you did not create them yourself, but e.g. used Microsoft
      Viva Insights. **NOTE: it is not recommended to use this feature for Outlook 365 calendars, because it is buggy:
      the Outlook platform keeps resetting the reminders once you involve an Outlook _client_, and once per
      minute, `focus-time` will set the reminder again, causing the Outlook client to show a reminder pop-up dialog
      every minute**
    - List of shell commands to run when a focus time event starts or ends, including the special commands `dnd-start`
      or `dnd-stop` which control your operating system's Do-Not-Disturb / Focus mode
    - The Windows _focus assist_ profile to be used ("Priority only" or "Alarms only")
- Ability to start (or stop) _ad-hoc_ focus time sessions for a configurable duration: the tool creates a blocker event
  in your calendar when _starting_ an adhoc session, or shortens the ongoing calendar event when _stopping_ an adhoc
  session)

## Installation

### Windows (10 and newer)

- Head over to the [Releases](https://github.com/focus-time/focus-time-app/releases) page and download the latest
  release for Windows
- Extract the downloaded zip archive
- Optional: move the extracted folder to a different location
- Open a CMD / PowerShell Window, navigate to the extracted folder, and call `focus-time.exe configure` to set up the
  Focus time app

### macOS (12 and newer)

- Head over to the [Releases](https://github.com/focus-time/focus-time-app/releases) page and download the latest
  release for macOS
- Since the application is not signed or notarized, you first have to remove the _quarantine flag_, e.g.
  via `sudo xattr -r -d com.apple.quarantine focus-time-app-macos-vx.y.z.zip`
- In Finder, double-click the downloaded zip archive to extract the application
- Optional: move the extracted folder to a different location
- Open a Terminal Window, navigate to the extracted folder, and call `./focus-time configure` to set up the Focus time
  app

## Usage

The **Focus time app** CLI comes with built-in documentation which you can access by
running `focus-time [command] --help`. Here is a brief overview of the available commands:

- `configure` checks your existing configuration for validity (if there is one), or lets you create a new configuration.
  All configuration options are interactively prompted. It sets up a regularly-triggered background job that calls
  the `sync` command once per minute
    - If you use a _personal_ Outlook 365 account, you can use the client ID `bcc815bb-01d0-4765-ae14-e2bf0ee22445`
    - If you use an Outlook 365 account _for work_, ask your company's Microsoft AAD admin to create a new _App
      registration_ on https://portal.azure.com. The _Redirect URL_ must be set to "Public client/native (mobile &
      desktop)" and point to `https://focus-time.github.io/focus-time-app`. Under _API permissions_,
      add _Microsoft Graph_ permissions for `Calendars.ReadWrite` and `offline_access`. The latter permission avoids
      that you need to constantly re-authenticate, by providing OIDC refresh tokens that are valid for 90 days
    - Once the configuration has completed successfully, the path to the configuration file is printed to the console.
      You can _change_ already-configured options there. On Windows, the file is located
      at `C:/Users/<your-username>/AppData/Roaming/FocusTimeApp/configuration.yaml`, on macOS you find it
      at `/Users/<your-username>/Library/Application Support/FocusTimeApp/configuration.yaml`
- `sync` Synchronizes the Do-Not-Disturb (Focus) state of your operating system with your focus
  time calendar events. If there is an active focus time calendar event, the Do-Not-Disturb mode (and other start
  commands you configured) is activated (unless this app already recently activated it). If there is no active
  calendar event (anymore), Do-Not-Disturb is deactivated again (if this app has set it), and other possibly configured
  stop commands are called
- `start <duration in minutes>` creates a new focus time calendar event in your configured calendar that starts _now_
  and ends in `duration` minutes. It then runs the `sync` command, so that your start command(s) are
  immediately executed
- `stop` stops an ongoing focus time calendar event, by shortening it so that it ends right now. Also runs the `sync`
  command internally, so that your configured stop command(s) are immediately executed.
- `uninstall` removes the scheduled background job (for the `sync` command) and Do-Not-Disturb helpers, if the operating
  system supports the removal
    - Note: on macOS, you have to manually open the _Shortcuts_ app and delete the `focus-time-app` shortcut yourself
- `version` prints the version of the tool

## Contributing & troubleshooting

If you encountered a problem or have a suggestion for improving the software, please head over to
the [Discussions](https://github.com/focus-time/focus-time-app/discussions) page.

Before you ask a _troubleshooting_ question, you may first want to look at the logs stored
under `C:/Users/<your-username>/AppData/Roaming/FocusTimeApp/` on Windows,
and under `/Users/<your-username>/Library/Application Support/FocusTimeApp/` on macOS. These logs often indicate what
is going wrong, providing guidance for how to fix the problem.

## Roadmap

Features that are missing but will eventually be implemented can be found on
the [Roadmap](https://github.com/orgs/focus-time/projects/1) page.

## Out of scope

For the time being, the implementation of the following features is **not** planned (but PRs or proposals are welcome):

- Supporting other calendar providers (except for those listed on the _Issues_ page)
- Synchronizing the state to other (mobile) devices
    - Note: macOS supports the synchronization of the Focus mode to your iPhone, out-of-the-box. For Android
      devices, there does not seem to be a solution, not even
      the [Phone Link](https://apps.microsoft.com/store/detail/phone-link/9NMPJ99VJBWV) app supports it. Adding our own
      support would be a lot of work and require a dedicated Android companion app, and a way for the desktop CLI to
      wake up the device
- GUI: adding a GUI (e.g. using PySide 6) would be a lot of work, but would have the benefit of adressing a much wider
  audience and facilitate the usage, and have the ability to show a tray icon
- Linux support
- Offering _signed_ binaries for macOS: we do not have an Apple _developer_ account, nor do we intend to pay extortion
  money to Apple. Also, implementing automated signing+notarization of the application is not trivial

## Development notes

- If you use PyCharm on Windows, in a _run configuration_ you need to enable the checkbox _Emulate terminal in output
  console_ so that retrieving passwords works
  properly ([background](https://youtrack.jetbrains.com/issue/PY-1823/getpass-should-accept-input-in-IDE-console))
