#!/bin/bash

###########################################################################
#
# Description： This script is used to start|stop|restart ttwx-server project
#
# uwsgi日志文件：/opt/ttwxenv/ttwx-log/uwsgi/server.log
# celery日志文件：/opt/ttwxenv/ttwx-log/celery/server.log
# django日志文件： /opt/ttwxenv/ttwx-log/djlog/application.log
#
###########################################################################

### 环境变量
scrip_name=$(basename $0)
env_dir=/opt/env
basedir=${env_dir}/noval-web
uwsgi_ini=${basedir}/uwsgi.ini
uwsgi_run=${basedir}/run/server.pid


### server服务的uwsgi脚本控制命令
start_uwsgi(){
    runcode=`ps aux | grep $uwsgi_ini | wc -l`
    if [ $runcode -gt 1 ]; then
        echo -e "\033[33mWarning noval-web uWSGI service already start\033[0m"
    else
        ${env_dir}/bin/uwsgi --chdir  $basedir --ini $uwsgi_ini
        if [ $? == 0 ]; then
            echo -e "Starting noval-web uWSGI service   \t\t\033[32m[Ok]\033[0m"
        else
            echo -e "Starting noval-web uWSGI service   \t\t\033[31m[Failure]\033[0m"
        fi
        echo "uWSGI  log: /opt/env/noval-web/logs/server.log"
    fi
    sleep 1
}

stop_uwsgi(){
    runcode=`ps aux | grep $uwsgi_ini | wc -l`
    if [ $runcode == 1 ]; then
        echo -e '\033[33mWarning noval-web uWSGI service is not running\033[0m'
    else
        ps aux|grep noval-web|grep -v grep|grep uwsgi|awk '{print $2}'|xargs kill -9

        if [ $? == 0 ]; then
            echo -e "Stopping noval-web uWSGI service   \t\t\033[32m[Ok]\033[0m"
        else
            echo -e "Stopping noval-web uWSGI service   \t\t\033[31m[Failure]\033[0m"
        fi
        rm -f $uwsgi_run
    fi
    sleep 2
}



status(){
    runcode=`ps aux | grep $uwsgi_ini|wc -l`
    if [ $runcode -gt 1 ]; then
        echo -e "\033[32mnoval-web uWSGI service is running\033[0m"
    else
        echo -e "\033[31mnoval-web uWSGI service is not running\033[0m"
    fi
}

Usage(){
    echo -e "\033[33mUsage: $scrip_name [action] [service]\033[0m"
    echo -e "[start uwsgi]:\t\tStart noval-web uWSGI service"
    echo -e "[stop  uwsgi]:\t\tStop noval-web uWSGI service"
    echo -e "[restart uwsgi]:\tRestart noval-web  uWSGI service"
    echo -e "[status server]: \tSee noval-web service status"
}

case "$1" in
    "start")
            start_uwsgi
            ;;
    "stop")
            stop_uwsgi
            ;;
    "restart")
            stop_uwsgi
            start_uwsgi
            ;;
    "status")
            status
            ;;
    *)
            Usage
            ;;
esac
