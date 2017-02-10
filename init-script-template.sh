#!/bin/bash

# chkconfig: 345 95 05

# Munki Enrollment Server (MES) Init Script.
# gdewitt@gsu.edu, 2015-06-15, 2015-06-15, 2016-03-04, 2016-03-14, 2016-04-25, 2016-07-06, 2016-08-02, 2016-08-09 (NetBoot Server Container)
# 2016-09-19, 2016-10-18, 2016-10-25.
# 2017-02-08
# to do: modify this script to work on distros besides RHEL

# References: See top level Read Me.

# Globals:
declare -x APP_NAME="Munki-Enrollment-Server"
declare -x APP_DISPLAY_NAME="Server for Munki Enrollment Client"
# System paths:
declare -x INIT_SCRIPTS_DIR="/etc/init.d"
declare -x SETSEBOOL="/usr/sbin/setsebool"
# System account for MES:
declare -x MES_RUN_AS_USER_NAME="__%MES_RUN_AS_USER_NAME%__"
declare -x MES_RUN_AS_USER_UID="__%MES_RUN_AS_USER_UID%__"

# Container:
declare -x THIS_SCRIPT=$(readlink -f "$0")
declare -x CONTAINER_DIR=$(dirname "$THIS_SCRIPT")
declare -x INIT_SCRIPT_SYMLINK="$INIT_SCRIPTS_DIR/$APP_NAME"

declare -x SERVER_HOSTNAME="$(hostname)"
declare -i CAN_START=0

# MES:
declare -x PYTHON_FILE_MES="$CONTAINER_DIR/__%MES_VENV_DIR_BASENAME%__/mes/server.py"
declare -x CMD_MES=(su "$MES_RUN_AS_USER_NAME" -p -c '"$CONTAINER_DIR/__%MES_VENV_DIR_BASENAME%__/bin/pypy" "$PYTHON_FILE_MES" > /dev/null 2>&1')
declare -a CONF_FILE_MES="$CONTAINER_DIR/__%MES_VENV_DIR_BASENAME%__/mes/configuration.plist"
declare -a CONF_FILE_MUNKI_CLIENT="$CONTAINER_DIR/__%MES_VENV_DIR_BASENAME%__/mes/munki_client_prefs.plist"
declare -a APP_FILES_ARRAY=("$PYTHON_FILE_MES" "$CONF_FILE_MES" "$CONF_FILE_MUNKI_CLIENT")
declare -a APP_CMDS_ARRAY=("CMD_MES")

# MARK: add_mes_system_account()
function add_mes_system_account() {
    # Attempts to add the system account:
    useradd -M "$MES_RUN_AS_USER_NAME" -c "System user for $APP_NAME." -u "$MES_RUN_AS_USER_UID"
    if [ "$?" == "0" ]; then
        echo "   Created user $MES_RUN_AS_USER_NAME."
    elif [ "$?" == "9" ]; then
        echo "   User $MES_RUN_AS_USER_NAME already exists."
    else
        echo "   ERROR: Could not create user $MES_RUN_AS_USER_NAME!"
    fi
}

# MARK: delete_mes_system_account()
function delete_mes_system_account() {
    # Attempts to delete the system account:
    userdel -f "$MES_RUN_AS_USER_NAME"
    if [ "$?" == "0" ]; then
        echo "   Deleted user $MES_RUN_AS_USER_NAME."
    elif [ "$?" == "6" ]; then
        echo "   User $MES_RUN_AS_USER_NAME does not exist."
    else
        echo "   Warning: Could not delete user $MES_RUN_AS_USER_NAME!"
    fi
}

# MARK: do_tests()
function do_tests() {
    # Performs some tests.
    # Assume can start unless something is wrong:
    CAN_START=1

    # Check for APP_FILES_ARRAY:
    files_missing=0
    files_missing_str=""
    for file in ${APP_FILES_ARRAY[@]}; do
        if [ ! -f "$file" ];then
            files_missing_str+="
            $file missing."
            files_missing=1
        fi
    done
    if [ "$files_missing" == "1" ];then
        CAN_START=0
        echo "--> Read config: ERROR: Missing these files: $files_missing_str"
    fi
}

# MARK: start()
function start() {
    echo "Reading config..."
    do_tests
    if [ "$CAN_START" == "0" ]; then
        echo "Cannot start.  Refer to previous messages.
To reconfigure, run: $0 install"
        exit 1
    fi
    echo "Starting $APP_DISPLAY_NAME..."
    # Start MES:
    echo "   Starting MES as user $MES_RUN_AS_USER_NAME..."
    "${CMD_MES[@]}" &
    if [ "$?" == "0" ]; then
        echo "   Started: ${CMD_MES[@]}"
    else
        echo "   ERROR: This failed to start: ${CMD_MES[@]}"
    fi
}

# MARK: stop()
function stop() {
    echo "Stopping $APP_DISPLAY_NAME..."
    # List container processes:
    echo "   Listing container processes..."
    container_pids="$(ps -ef | grep -v grep | grep "$CONTAINER_DIR" | awk '{print $2}')"
    eval 'container_pid_array=($container_pids)'
    echo "   Found ${#container_pid_array[@]} running processes in $CONTAINER_DIR..."
    for p in "${container_pid_array[@]}"; do
        kill $p > /dev/null 2>&1 || echo "   ERROR: This PID failed to stop: $p"
    done
    echo "$APP_DISPLAY_NAME stopped."
}

# MARK: reload()
function reload() {
    echo "Reloading $APP_DISPLAY_NAME..."
    stop
    sleep 5
    start
    echo "$APP_DISPLAY_NAME reloaded."
}

# MARK: install()
function install() {
    echo "Installing $APP_DISPLAY_NAME..."
    if [ "$EUID" != "0" ]; then
        echo "ERROR: Must be root to install $APP_DISPLAY_NAME."
        exit 2
    fi

    # User interaction for setting config:
    echo "   Pause for a moment and edit or restore your MES configuration file at:"
    echo "   $CONF_FILE_MES"
    echo "   Press return when you have this file in place."
    read dummy_var
    echo "   Now edit or restore your Munki client configuration template at:"
    echo "   $CONF_FILE_MUNKI_CLIENT"
    echo "   Press return when you have this file in place."
    read dummy_var
    # Read config:
    do_tests
    # Add service user if necessary:
    add_mes_system_account && echo "   Ran command to add user $MES_RUN_AS_USER_NAME."

    echo "   App display name: $APP_DISPLAY_NAME"
    echo "   Init script will be copied to: $INIT_SCRIPTS_DIR/$APP_NAME"
    echo "   Container path: $CONTAINER_DIR"

    # Make sure everything is stopped. Installs should be idempotent.
    echo "Calling stop()..."
    stop
    # Set permissions:
    echo "Copying and setting permissions..."
    chown -R "$MES_RUN_AS_USER_NAME":root "$CONTAINER_DIR" && echo "   Set ownership for $CONTAINER_DIR."
    chmod -R 0770 "$CONTAINER_DIR" && echo "   Set permissions for $CONTAINER_DIR."
    # Create init script symlink:
    if [ -e "$INIT_SCRIPT_SYMLINK" ]; then
        rm "$INIT_SCRIPT_SYMLINK"
    fi
    ln -s "$THIS_SCRIPT" "$INIT_SCRIPT_SYMLINK" && echo "   Created symlink: $INIT_SCRIPT_SYMLINK."
    chown root:root "$INIT_SCRIPT_SYMLINK" && echo "   Set ownership for $INIT_SCRIPT_SYMLINK."
    # Set SELinux booleans for http:
    if [ -f "$SETSEBOOL" ]; then
        echo "Applying SELinux settings for http..."
        "$SETSEBOOL" -P httpd_can_network_connect true && echo "   httpd_can_network_connect is true"
        "$SETSEBOOL" -P httpd_use_nfs true && echo "   httpd_use_nfs is true"
    fi
    # Start:
    echo "Calling start()..."
    start
    # Set startup:
    echo "Running chkconfig..."
    /sbin/chkconfig --level 345 "$APP_NAME" on && echo "  App will run on system boot."

    echo "Finished installation."
}

# MARK: uninstall()
function uninstall() {
    echo "Removing $APP_DISPLAY_NAME..."
    if [ "$EUID" != "0" ]; then
        echo "ERROR: Must be root to remove $APP_DISPLAY_NAME."
        exit 2
    fi

    # Make sure everything is stopped.
    echo "Calling stop()..."
    stop

    echo "Running chkconfig..."
    /sbin/chkconfig --level 345 "$APP_NAME" off && echo "  App will NOT run on system boot."

    # Delete init script symlink:
    if [ -e "$INIT_SCRIPT_SYMLINK" ]; then
        rm "$INIT_SCRIPT_SYMLINK" && echo "   Removed symlink: $INIT_SCRIPT_SYMLINK"
    fi

    # Delete service user if necessary:
    delete_mes_system_account && echo "   Ran command to remove user $MES_RUN_AS_USER_NAME."

    echo "Uninstall complete."
}

# MARK: help()
function help() {
    echo "Usage: $0 [start|stop|reload|install|uninstall]"
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    reload)
        reload
        ;;
    restart)
        reload
        ;;
    install)
        install
        ;;
    uninstall)
        uninstall
        ;;
    *)
        help
        ;;
esac
exit 0
