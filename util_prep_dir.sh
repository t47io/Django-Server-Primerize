mkdir backup

mkdir cache
touch cache/log_alert_admin.log cache/log_cron.log cache/log_django.log cache/log_cron_cleanup.log cache/log_cron_backup.log cache/log_cron_gdrive.log cache/log_cron_report.log cache/log_cron_version.log
touch cache/stat_backup.txt cache/stat_sys.txt

cp -n config/arg.conf.example config/arg.conf
cp -n config/cron.conf.example config/cron.conf
cp -n config/env.conf.example config/env.conf
cp -n config/oauth.conf.example config/oauth.conf
cp -n config/t47_dev.py.example config/t47_dev.py

mkdir data
mkdir data/1d data/2d data/3d

mkdir media/css/min
mkdir media/js/admin/min media/js/public/min media/js/suit/min

mkdir src/pymerize/__pycache__

./util_chmod.sh