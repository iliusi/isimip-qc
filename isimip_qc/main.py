import argparse
import logging

from .checks import checks
from .config import settings
from .models import File
from .utils.files import copy_file, move_file, walk_files

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Check ISIMIP files for matching protocol definitions')
    # mandatory
    parser.add_argument('schema_path', help='ISIMIP schema_path, e.g. ISIMIP3a/OutputData/water_global')
    # optional
    parser.add_argument('-c', '--copy', dest='move', action='store_true', default=None,
                        help='Copy checked files to CHECKED_PATH')
    parser.add_argument('-m', '--move', dest='move', action='store_true', default=None,
                        help='Move checked files to CHECKED_PATH')
    parser.add_argument('--config-file', dest='config_file', default=None,
                        help='File path to the config file')
    parser.add_argument('--unchecked-path', dest='unchecked_path', default=None,
                        help='base path of the unchecked files')
    parser.add_argument('--checked-path', dest='checked_path', default=None,
                        help='base path for the checked files')
    parser.add_argument('--pattern-location', dest='pattern_locations', default=None,
                        help='URL or file path to the pattern json')
    parser.add_argument('--schema-location', dest='schema_locations', default=None,
                        help='URL or file path to the json schema')
    parser.add_argument('--log-level', dest='log_level', default=None,
                        help='Log level (ERROR, WARN, INFO, or DEBUG)')
    parser.add_argument('--log-path', dest='log_path', default=None,
                        help='base path for the log files for individual files')
    parser.add_argument('-f', '--first-file', dest='first_file', action='store_true', default=False,
                        help='only process first file found in UNCHECKED_PATH')
    parser.add_argument('-w', '--stop-on-warnings', dest='stop_warn', action='store_true', default=False,
                        help='stop execution on warnings')
    parser.add_argument('-e', '--stop-on-errors', dest='stop_err', action='store_true', default=False,
                        help='stop execution on errors')

    # setup
    args = parser.parse_args()
    settings.setup(args)

    if settings.PATTERN is None:
        parser.error('no pattern could be found.')
    if settings.SCHEMA is None:
        parser.error('no schema could be found.')

    # walk over unchecked files
    for file_path in walk_files(settings.UNCHECKED_PATH):
        print(f"\033[93mChecking : %s\033[0m" % file_path)
        if file_path.suffix in settings.PATTERN['suffix']:
            file = File(file_path)
            file.open()
            file.match()
            for check in checks:
                check(file)
            file.validate()
            file.close()

            if file.has_warnings or file.has_errors:
                file.clean = False
                print(f"\033[91mFile did not pass all checks\033[0m")
            else:
                print(f"\033[92mFile has passed all checks\033[0m")

            if file.has_warnings and settings.STOP_WARN:
                break
            if file.has_errors and settings.STOP_ERR:
                break

            if settings.MOVE and settings.CHECKED_PATH and file.clean:
                if settings.MOVE:
                    print('Moving file to CHECKED_PATH')
                    move_file(settings.UNCHECKED_PATH / file.path, settings.CHECKED_PATH / file.path)
                elif settings.COPY:
                    print('Copying file to CHECKED_PATH')
                    copy_file(settings.UNCHECKED_PATH / file.path, settings.CHECKED_PATH / file.path)
        else:
            logger.error('%s has wrong suffix. Use "%s" for this simulation round', file_path, settings.PATTERN['suffix'][0])

        print()

        if settings.FIRST_FILE:
            break
