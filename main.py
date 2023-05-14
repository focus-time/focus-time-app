from cli.cli import app
from utils.compatibility_checker import check_os_compatibility

if __name__ == '__main__':
    # TODO single access lock check
    check_os_compatibility()
    app()
