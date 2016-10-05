import logging
import yaml

from ..Config import ConfigInstall


def setup_logging(application_name='PyDvi',
                  config_file=ConfigInstall.Logging.default_config_file):

    logging_config_file_name = ConfigInstall.Logging.find(config_file)
    logging_config = yaml.load(open(logging_config_file_name, 'r'))

    # Fixme: \033 is not interpreted in YAML
    formatter_config = logging_config['formatters']['ansi']['format']
    logging_config['formatters']['ansi'][
        'format'] = formatter_config.replace('<ESC>', '\033')

    logger = logging.getLogger(application_name)

    return logger
