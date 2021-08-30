from ambra_sdk.api import Api

from ambramelin.util import credentials
from ambramelin.util.config import env_selected, load_config
from ambramelin.util.errors import NoEnvironmentSelectedError


def get_api() -> Api:
    config = load_config()

    if not env_selected(config):
        raise NoEnvironmentSelectedError()

    assert config.current is not None
    env = config.envs[config.current]

    assert env.user is not None
    cred_manager = credentials.managers[config.users[env.user].credentials_manager]

    return Api(env.url, username=env.user, password=cred_manager.get_password(env.user))
