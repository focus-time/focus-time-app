# Helpful resources:
# https://apple.stackexchange.com/questions/340942/applescript-how-can-i-get-ui-elements-names-attributes-properties-classe/340943#340943
# https://n8henrie.com/2013/03/a-strategy-for-ui-scripting-in-applescript/  --> write "UI elements" to get a list of UI elements

tell application "System Events" to tell process "Shortcuts"
	set frontmost to true
	delay 1

	#tell scroll area 1 of group 1 of window 1
    #    click button 2
    #end tell

    tell window 1
        UI elements
    end tell

end tell
