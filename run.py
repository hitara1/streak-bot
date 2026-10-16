#!/usr/bin/env python3
"""Entry point for Habit Streak Bot"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.main import main

if __name__ == "__main__":
    main()
