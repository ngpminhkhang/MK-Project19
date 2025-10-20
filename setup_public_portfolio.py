#!/usr/bin/env python
"""
Script để tạo portfolio public cho demo
Chạy script này sau khi deploy để tạo portfolio mẫu cho khách xem
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command

def main():
    print("Creating public portfolio...")
    try:
        call_command('create_public_portfolio')
        print("✅ Public portfolio created successfully!")
    except Exception as e:
        print(f"❌ Error creating public portfolio: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
