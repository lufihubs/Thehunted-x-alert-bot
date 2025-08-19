from setuptools import setup, find_packages

setup(
    name="telegram-solana-alert-bot",
    version="2.0.0",
    description="Enhanced Telegram bot for Solana token price alerts",
    author="Your Name",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "python-telegram-bot==20.3",
        "aiosqlite==0.19.0",
        "httpx==0.24.1",
        "asyncio-mqtt==0.16.1"
    ],
    entry_points={
        "console_scripts": [
            "telegram-bot=railway_start:main",
        ],
    },
)
