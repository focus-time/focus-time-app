import os.path
import sys
main_folder_path = os.path.dirname(os.path.dirname(__file__))
if main_folder_path not in sys.path:
    sys.path.append(main_folder_path)
from focus_time_app.cli.cli import app
from focus_time_app.utils.compatibility_checker import check_os_compatibility

if __name__ == '__main__':
    # TODO single access lock check
    check_os_compatibility()
    app()
