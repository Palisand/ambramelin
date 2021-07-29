from ambramelin.util.config import Config
from ambra_sdk.service.filtering import FilterCondition


class AmbramelinError(Exception):
    pass


class EnvironmentAlreadyExistsError(AmbramelinError):
    def __init__(self, env: str) -> None:
        super().__init__(f"Environment '{env}' already exists.")


class EnvironmentNotFoundError(AmbramelinError):
    def __init__(self, env: str, config: Config) -> None:
        super().__init__(
            f"Environment '{env}' not found. Must be one of {list(config['envs'])}."
        )


class InvalidFilterConditionError(AmbramelinError):
    def __init__(self, condition: str) -> None:
        super().__init__(
            f"'{condition}' is not a valid filter condition."
            f"Must be one of {[f.value for f in FilterCondition]}."
        )


class NoEnvironmentsError(AmbramelinError):
    def __init__(self) -> None:
        super().__init__("No environments added.")


class NoEnvironmentSelectedError(AmbramelinError):
    def __init__(self) -> None:
        super().__init__("No environment selected.")


class NoUsersError(AmbramelinError):
    def __init__(self) -> None:
        super().__init__("No users added.")


class UserAlreadyExistsError(AmbramelinError):
    def __init__(self, user: str) -> None:
        super().__init__(f"Used '{user}' already exists.")


class UserNotFoundError(AmbramelinError):
    def __init__(self, user: str, config: Config) -> None:
        super().__init__(
            f"User '{user}' not found. Must be one of {list(config['users'])}."
        )
