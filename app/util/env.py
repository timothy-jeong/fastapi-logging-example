import os
import logging


logger = logging.getLogger(__name__)

def get_bool_from_env(env_var_name: str, default: bool = False) -> bool:
    """
    환경변수에서 boolean 값을 얻는다.
    
    Args:
        env_var_name: 얻고자하는 환경변수 이름.
        default: 환경변수가 없거나 값이 잘못되었을 경우 얻을 값.

    Returns:
        환경 변수의 boolean 값 또는 설정되지 않았거나 유효하지 않은 경우 기본값.
    """
    env_var = os.getenv(env_var_name)

    if env_var is None:
        logger.warning(f"{env_var_name} environment variable not set. Using default: {default}")
        return default

    # Check for various true/false string representations (case-insensitive)
    true_values = ("true", "1", "t", "y", "yes")
    false_values = ("false", "0", "f", "n", "no")

    env_var_lower = env_var.lower()

    if env_var_lower in true_values:
        try:
            return bool(strtobool(env_var))  # Attempt strict conversion
        except ValueError:
            logger.warning(f"Invalid value for {env_var_name}: '{env_var}'. Using default: {default}")
            return default
    elif env_var_lower in false_values:
        return False
    else:
        logger.warning(f"Invalid value for {env_var_name}: '{env_var}'. Using default: {default}")
        return default
    
def strtobool(val):
    """Convert a string representation of truth to true (1) or false (0).

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return 1
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return 0
    else:
        raise ValueError("invalid truth value %r" % (val,))
