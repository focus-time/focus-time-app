#!/bin/bash

set -ex

# Starts the Shortcuts app, it should show the dialog that asks the user to confirm installing the shortcut
open resources/focus-time-app.shortcut

sleep 10

# Clicks the button to install the shortcut
osascript .github/macos-hacks/install-shortcut-unattended.scpt

# Verifies that the shortcut has been installed
shortcuts list
