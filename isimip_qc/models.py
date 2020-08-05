import logging

from .config import settings
from .utils.netcdf import open_dataset


class File(object):

    def __init__(self, file_path):
        self.path = file_path.relative_to(settings.UNCHECKED_PATH)
        self.abs_path = file_path
        self.identifiers = {}
        self.clean = True
        self.logger = None
        self.dataset = None

    def open(self):
        self.dataset = open_dataset(self.abs_path)
        self.logger = self.get_logger()
        self.info('Open %s.', self.abs_path)

    def close(self):
        self.dataset.close()
        for handler in self.logger.handlers:
            handler.close()
        self.info('Close %s.', self.abs_path)

    def info(self, *args, **kwargs):
        self.logger.info(*args, **kwargs)

    def warn(self, *args, **kwargs):
        self.logger.warn(*args, **kwargs)

    def error(self, *args, **kwargs):
        self.logger.error(*args, **kwargs)
        self.clean = False  # this file should not be moved!

    def get_logger(self):
        # setup a log handler for the command line and one for the file
        logger_name = str(self.path)
        logger = logging.getLogger(logger_name)

        # do not propagate messages to the root logger,
        # which is configured in settings.setup()
        logger.propagate = False

        # set the log level to INFO, so that it is not influeced by settings.LOG_LEVEL
        logger.setLevel(logging.INFO)

        # add handlers
        logger.addHandler(self.get_stream_handler())
        if settings.LOG_PATH:
            logger.addHandler(self.get_file_handler())

        return logger

    def get_stream_handler(self):
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')

        handler = logging.StreamHandler()
        handler.setLevel(settings.LOG_LEVEL)
        handler.setFormatter(formatter)

        return handler

    def get_file_handler(self):
        log_path = settings.LOG_PATH / self.path.with_suffix('.log')
        log_path.parent.mkdir(parents=True, exist_ok=True)

        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

        handler = logging.FileHandler(log_path)
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)

        return handler

    def match_identifiers(self):
        match = settings.PATTERN['file'].match(self.path.name)
        if match:
            for key, value in match.groupdict().items():
                if value is not None:
                    if value.isdigit():
                        self.identifiers[key] = int(value)
                    else:
                        self.identifiers[key] = value

            self.info('File matched: %s.', self.identifiers)
        else:
            self.error('File did not match.')
