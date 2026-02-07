"""
日志配置模块
提供统一的日志配置，支持文件滚动存储和控制台输出
"""
import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from typing import Optional

from app.core.config import settings


# 日志目录（使用配置中的路径）
LOG_DIR = Path(__file__).parent.parent.parent / settings.LOG_DIR
LOG_DIR.mkdir(exist_ok=True)


# 日志级别映射
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def get_log_level(level_str: str) -> int:
    """将字符串日志级别转换为 logging 模块常量"""
    return LOG_LEVEL_MAP.get(level_str.upper(), logging.INFO)


class ColoredFormatter(logging.Formatter):
    """带颜色的控制台日志格式化器"""

    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
    }
    RESET = '\033[0m'

    def format(self, record):
        # 添加颜色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        # 格式化消息
        result = super().format(record)
        # 恢复原始 levelname（避免影响其他 handler）
        record.levelname = levelname
        return result


class AutoFlushTimedRotatingFileHandler(TimedRotatingFileHandler):
    """自动 flush 的定时滚动文件处理器"""

    def emit(self, record):
        """重写 emit 方法，每次写入后自动 flush"""
        super().emit(record)
        self.flush()


def setup_logger(
    name: str = "app",
    log_file: Optional[str] = None,
    level: Optional[int] = None
) -> logging.Logger:
    """
    设置并返回一个配置好的 logger

    Args:
        name: logger 名称
        log_file: 日志文件名（不含路径），默认为 app.log（所有日志写入同一个文件）
        level: 日志级别，默认使用配置文件中的 LOG_LEVEL

    Returns:
        配置好的 logger 实例
    """
    if level is None:
        level = get_log_level(settings.LOG_LEVEL)

    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False  # 不传递给父 logger

    # 日志格式
    log_format = "[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # 1. 控制台处理器（带颜色）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = ColoredFormatter(
        fmt=log_format,
        datefmt=date_format
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 2. 文件处理器（所有 logger 共享同一个文件处理器）
    # 使用全局共享的文件 handler，避免重复添加
    _get_file_handler(level, log_format, date_format, log_file)
    logger.addHandler(_get_file_handler(level, log_format, date_format, log_file))

    # 配置 SQLAlchemy 日志级别 - 只显示 WARNING 及以上
    _configure_sqlalchemy_logger()

    return logger


def _configure_sqlalchemy_logger():
    """配置 SQLAlchemy 日志级别，只显示 WARNING 及以上"""
    # 设置 SQLAlchemy engine 日志级别为 WARNING
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    # 设置 SQLAlchemy pool 日志级别为 WARNING
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    # 设置 SQLAlchemy ORM 日志级别为 WARNING
    logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)
    # 设置 SQLAlchemy 其他日志级别为 WARNING
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


# 全局共享的文件 handler
_file_handler: Optional[AutoFlushTimedRotatingFileHandler] = None


def _get_file_handler(level: int, log_format: str, date_format: str, log_file: Optional[str] = None) -> AutoFlushTimedRotatingFileHandler:
    """
    获取或创建全局共享的文件处理器

    所有 logger 共享同一个文件，便于排查问题
    """
    global _file_handler
    if _file_handler is not None:
        return _file_handler

    if log_file is None:
        log_file = "app.log"

    file_path = LOG_DIR / log_file
    _file_handler = AutoFlushTimedRotatingFileHandler(
        filename=str(file_path),
        when="midnight",           # 每天午夜滚动
        interval=1,                # 每天一个文件
        backupCount=7,             # 保留7天
        encoding="utf-8",
        delay=False                # 立即创建文件
    )
    _file_handler.setLevel(level)
    _file_handler.suffix = "%Y-%m-%d"  # 滚动文件名后缀：app.log.2026-01-07

    # 文件日志格式（不带颜色）
    file_formatter = logging.Formatter(
        fmt=log_format,
        datefmt=date_format
    )
    _file_handler.setFormatter(file_formatter)

    return _file_handler


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的 logger

    Args:
        name: logger 名称，通常使用 __name__

    Returns:
        logger 实例
    """
    # 检查是否已配置
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
