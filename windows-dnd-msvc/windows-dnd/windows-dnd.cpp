// Based on code written by Rafael Rivera, see https://gist.github.com/riverar/085d98ffb1343e92225a10817109b2e3
/*
To get the project working, the following was done:
1) Put the quiethours.idl file into the Visual Studio project
2) Hack the quiethours.idl file, removing the invalid empty _QH_PROFILE_DATA struct, and the GetAllProfileData() method referencing it
3) In VS right click the idl file and click "Compile", which generates the .c and .h file
4) Manually add the .c and .h file to the project
*/

#include <iostream>
#include <windows.h>
#include <atlbase.h>
#include "quiethours_h.h"
#include <string>

//Returns the last Win32 error, in string format. Returns an empty string if there is no error.
std::string GetLastErrorAsString()
{
	//Get the error message ID, if any.
	DWORD errorMessageID = ::GetLastError();
	if (errorMessageID == 0) {
		return std::string(); //No error message has been recorded
	}

	LPSTR messageBuffer = nullptr;

	//Ask Win32 to give us the string version of that message ID.
	//The parameters we pass in, tell Win32 to create the buffer that holds the message for us (because we don't yet know how long the message string will be).
	size_t size = FormatMessageA(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
		NULL, errorMessageID, MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), (LPSTR)&messageBuffer, 0, NULL);

	//Copy the error message into a std::string.
	std::string message(messageBuffer, size);

	//Free the Win32's string's buffer.
	LocalFree(messageBuffer);

	return message;
}

bool cmdOptionExists(char** begin, char** end, const std::string& option)
{
	return std::find(begin, end, option) != end;
}

std::wstring profileUnrestricted = L"Microsoft.QuietHoursProfile.Unrestricted";
std::wstring profilePriorityOnly = L"Microsoft.QuietHoursProfile.PriorityOnly";
std::wstring profileAlarmsOnly = L"Microsoft.QuietHoursProfile.AlarmsOnly";

/*
Call this program with one of the following codes:

"get-profile": Determines the currently-configured "quiet mode", printing either "off", "priority-only" or "alarms-only".
	   Returns 1 if something goes wrong, printing the last failed command.

"set-priority-only": sets the quiet mode to "Priority only". Returns 1 if something goes wrong, printing the last failed command.

"set-alarms-only": sets the quiet mode to "Alarms only". Returns 1 if something goes wrong, printing the last failed command.

"set-off": disables the quiet mode. Returns 1 if something goes wrong, printing the last failed command.
*/
int main(int argc, char* argv[])
{
	if (FAILED(CoInitialize(nullptr))) {
		std::cout << "Unable to initialize COM interface: " << GetLastErrorAsString();
		return 1;
	}

	CComPtr<IQuietHoursSettings> quietHoursSettings;
	if FAILED(CoCreateInstance(CLSID_QuietHoursSettings, nullptr, CLSCTX_LOCAL_SERVER, IID_PPV_ARGS(&quietHoursSettings))) {
		std::cout << "Unable to retrieve COM pointer to IQuietHoursSettings: " << GetLastErrorAsString();
		return 1;
	}

	if (cmdOptionExists(argv, argv + argc, "get-profile")) {
		CComHeapPtr<wchar_t> profileId;
		if (FAILED(quietHoursSettings->get_UserSelectedProfile(&profileId))) {
			std::cout << "Unable to retrieve selected quiet hours profile: " << GetLastErrorAsString();
			return 1;
		}

		//std::wcout << L"Current profile: " << static_cast<LPWSTR>(profileId) << std::endl << std::endl;

		std::wstring profileStr(profileId);
		if (profileStr.compare(profileUnrestricted) == 0) {
			std::cout << "off";
			return 0;
		}
		if (profileStr.compare(profilePriorityOnly) == 0) {
			std::cout << "priority-only";
			return 0;
		}
		if (profileStr.compare(profileAlarmsOnly) == 0) {
			std::cout << "alarms-only";
			return 0;
		}
		std::wcout << "Unrecognized profile: " << profileStr;
		return 1;
	}
	else if (cmdOptionExists(argv, argv + argc, "set-priority-only") || cmdOptionExists(argv, argv + argc, "set-alarms-only")
		|| cmdOptionExists(argv, argv + argc, "set-off")) {
		std::wstring profileToSet = profileUnrestricted;
		if (cmdOptionExists(argv, argv + argc, "set-priority-only")) profileToSet = profilePriorityOnly;
		if (cmdOptionExists(argv, argv + argc, "set-alarms-only")) profileToSet = profileAlarmsOnly;

		if (FAILED(quietHoursSettings->put_UserSelectedProfile(&profileToSet[0]))) {
			std::wcout << "Unable to set profile " << profileToSet;
			std::cout << GetLastErrorAsString() << std::endl;
			return 1;
		}
	}
	else {
		std::cout << "Call this application with a command!" << std::endl;
		return 1;
	}
}
