import os


def load_dotenv(dotenv_path='.env'):
    """
    加载环境变量
    """
    if os.path.isfile(dotenv_path):
        with open(dotenv_path) as dotenv_file:
            for line in dotenv_file:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    else:
        print(f"Warning: {dotenv_path} file not found.")


def get_dotenv_value(key, default_value=None):
    """
    获取环境变量的值
    """
    return os.getenv(key, default_value)