from datetime import datetime
import logging,os

from logging.handlers import RotatingFileHandler

class ColorFormatter(logging.Formatter):
    """自定义彩色日志格式"""
    grey = "\x1b[38;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    COLORS = {
        logging.DEBUG: grey,
        logging.INFO: green,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: bold_red
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.grey)
        formatter = logging.Formatter(
            f"{color}%(levelname)s - %(asctime)s :{self.reset}     %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        fillFormatter = logging.Formatter(
            f"{color}%(levelname)s - %(asctime)s :    %(message)s{self.reset} ",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        if record.levelno != logging.INFO:
            return fillFormatter.format(record)
        return formatter.format(record)

def setup_logging():
    # 确保日志目录存在
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)  # 关键修复：自动创建目录
    
    logger = logging.getLogger("business")
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()  # 清除现有处理器

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # 控制台只显示 INFO 及以上级别
    
    
    
    # 文件处理器（带错误处理）
    try:
        log_filename = f"app_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = RotatingFileHandler(
            filename=os.path.join(log_dir, log_filename),  # 日志名包含日期
            # when="midnight",  # 每天午夜滚动
            backupCount=7,     # 保留7天日志
            maxBytes=10 * 1024 * 1024,  # 10MB
            encoding='utf-8'
        )
    except Exception as e:
        logger.warning(f"无法创建日志文件: {str(e)}")
        file_handler = logging.NullHandler()  # 回退到空处理器

    # 统一格式
    formatter = logging.Formatter(
        '%(levelname)s - %(asctime)s :     %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(ColorFormatter())
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # 统一接管 uvicorn 日志
    for log_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        uvicorn_log = logging.getLogger(log_name)
        uvicorn_log.handlers.clear()
        uvicorn_log.propagate = False
        uvicorn_log.addHandler(console_handler)
        uvicorn_log.addHandler(file_handler)
    
    return logger

logger = setup_logging()
