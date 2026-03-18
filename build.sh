#!/usr/bin/env bash
# Kích hoạt bàn tay sắt: Dừng toàn bộ hệ thống ngay lập tức nếu phát hiện lỗi
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate