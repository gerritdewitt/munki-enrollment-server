#!/bin/bash

#  build-script.sh
#  Munki Enrollment Server (MES)
#  Script for for creating an installable "container"
#  for running the MES on Linux.

# Written by Gerrit DeWitt (gdewitt@gsu.edu)
# gdewitt@gsu.edu, 2016-07-06, 2016-08-11 (NetBoot Server Container).
# 2016-09-19, 2016-10-25.
# Copyright Georgia State University.
# This script uses publicly-documented methods known to those skilled in the art.
# References: See top level Read Me.

# MARK: VARIABLES

# Variables for package:
declare -x THIS_DIR=$(dirname "$0")
declare -x PACKAGE_ROOT_DIR="$THIS_DIR/munki-enrollment-server"
declare -x PACKAGE_TARBALL=""
declare -x STAGING_DIR="$THIS_DIR/staging"
declare -x PACKAGE_VERSION=""
declare -x MES_RUN_AS_USER_NAME=""
declare -x MES_RUN_AS_USER_UID=""

# Paths:
# scripts and logs:
declare -x INIT_SCRIPT_TEMPLATE_PATH="$THIS_DIR/init-script-template.sh"
declare -x INIT_SCRIPT_PATH="$PACKAGE_ROOT_DIR/init-script.sh"
declare -x BUILD_LOG_PATH="$PACKAGE_ROOT_DIR/build.log"
# pypy:
declare -x PYPY_STAGING_DIR="$STAGING_DIR/src-pypy"
declare -x PYPY_VENV_BIN="$PYPY_STAGING_DIR/bin/virtualenv-pypy"
# mes:
declare -x MES_STAGING_DIR="$THIS_DIR/src-mes"
declare -x MES_VENV_DIR="$PACKAGE_ROOT_DIR/mes_virtualenv"
declare -x MES_CODE_DIR="$MES_VENV_DIR/mes"

# URLs:
declare -x PYPY_PAGE_URL="https://github.com/squeaky-pl/portable-pypy#portable-pypy-distribution-for-linux"
declare -x PYPY_HREF_LABEL="PyPy\s\d*.*\sx86_64" # Example: PyPy 5.3.3 x86_64

# Dependencies:
declare -a MES_DEPENDENCIES=("pyasn1" "idna" "enum34" "ipaddress" "six" "cryptography" "pyOpenSSL" "itsdangerous" "MarkupSafe" "Jinja2" "Werkzeug" "Flask")

# MARK: pre_cleanup()
# Sets up environment.
function pre_cleanup(){
    if [ -d "$STAGING_DIR" ]; then
        rm -fr "$STAGING_DIR" && echo "Removed $STAGING_DIR."
    fi
    if [ -d "$PACKAGE_ROOT_DIR" ]; then
        rm -fr "$PACKAGE_ROOT_DIR" && echo "Removed $PACKAGE_ROOT_DIR."
    fi
    mkdir -p "$STAGING_DIR" && echo "Created $STAGING_DIR."
    mkdir -p "$PACKAGE_ROOT_DIR" && echo "Created $PACKAGE_ROOT_DIR."
    touch "$BUILD_LOG_PATH"
    log_and_print "Build started: $(date)"
    log_and_print "Build version: $PACKAGE_VERSION"
}

# MARK: gather_info()
function gather_info(){
    echo "Enter a version number for this build (for example YYYY.MM like 2016.07):"
    read PACKAGE_VERSION
    package_root_dir_basename="$(basename "$PACKAGE_ROOT_DIR")"
    PACKAGE_TARBALL="$THIS_DIR/$package_root_dir_basename-$PACKAGE_VERSION.tgz"
    echo "The MES should be run with the privileges of a system user account other than root."
    echo "Please specify the system account that the init script will create:"
    echo "   -> Munki Enrollment Server system account name (example: munki-enrollment-server):"
    read MES_RUN_AS_USER_NAME
    echo "   -> Munki Enrollment Server system account UID (example: 502):"
    read MES_RUN_AS_USER_UID
}

# MARK: write_init_script()
function write_init_script(){
    MES_VENV_DIR_BASENAME="$(basename "$MES_VENV_DIR")"
    init_script_template_contents="$(cat $INIT_SCRIPT_TEMPLATE_PATH)"
    init_script_contents="$(echo "$init_script_template_contents" | sed "s|__%MES_VENV_DIR_BASENAME%__|$MES_VENV_DIR_BASENAME|g" | sed "s|__%MES_RUN_AS_USER_NAME%__|$MES_RUN_AS_USER_NAME|g" | sed "s|__%MES_RUN_AS_USER_UID%__|$MES_RUN_AS_USER_UID|g")"
    echo "$init_script_contents" > "$INIT_SCRIPT_PATH"
    log_and_print "Created init script ($INIT_SCRIPT_PATH) from template."
    chmod 0755 "$INIT_SCRIPT_PATH"
    log_and_print "Set permissions on init script."
}

# MARK: download_and_extract_pypy()
function download_and_extract_pypy(){
    download_page_html="$(curl "$PYPY_PAGE_URL")"
    filtered_html="$(echo "$download_page_html" | grep "a href" | grep "$PYPY_HREF_LABEL")"
    download_url="$(echo "$filtered_html" | sed "s|<a href=\"||g" | sed "s|</*[\s*A-Za-z\s*]*>||g" | awk -F'\"' '{print $1}')"
    log_and_print "Download URL appears to be: $download_url"
    file_basename="$(echo "$download_url" | awk -F'/' '{print $NF}')"
    log_and_print "Downloading to staging dir as: $file_basename"
    curl -L "$download_url" > "$STAGING_DIR/$file_basename"
    if [ ! -f "$STAGING_DIR/$file_basename" ]; then
        log_and_print "ERROR: Failed to download pypy!"
        exit 1
    fi
    log_and_print "Done with download."
    log_and_print "Extracting: $file_basename"
    mkdir -p "$PYPY_STAGING_DIR"
    tar -xv -C "$PYPY_STAGING_DIR" -f "$STAGING_DIR/$file_basename"
    if [ "$?" != "0" ]; then
        log_and_print "ERROR: Failed extract pypy!"
        exit 1
    fi
    mv "$PYPY_STAGING_DIR"/*/* "$PYPY_STAGING_DIR"
    log_and_print "Extracted pypy material to: $PYPY_STAGING_DIR"
}

# MARK: create_venv()
function create_venv(){
    item_name="$1"
    venv_tmp_dir_path="$STAGING_DIR/tmp-venv"
    venv_dir_path="$2"
    staging_dir_path="$3"
    code_dir_path="$4"
    declare -a dependencies_array=("${!5}")
    log_and_print "Creating Python venv for $item_name: $venv_dir_path"
    "$PYPY_VENV_BIN" --system-site-packages --always-copy "$venv_dir_path"
    if [ "$?" != "0" ]; then
        log_and_print "ERROR: Failed to create Python venv for $item_name!"
        exit 1
    fi
    # Get rid of symlinks in venvs; yes, despite --always-copy:
    mv "$venv_dir_path" "$venv_tmp_dir_path"
    rsync -urL "$venv_tmp_dir_path"/ "$venv_dir_path"
    rm -fr "$venv_tmp_dir_path"
    # Copy libraries that venv omitted.  Crudely:
    rm -fr "$venv_dir_path/lib_pypy"
    cp -R "$PYPY_STAGING_DIR/lib_pypy" "$venv_dir_path/lib_pypy"
    rm -fr "$venv_dir_path/lib-python"
    cp -R "$PYPY_STAGING_DIR/lib-python" "$venv_dir_path/lib-python"
    log_and_print "Python venv for $item_name created.  Activating..."
    source "$venv_dir_path"/bin/activate && log_and_print "Python venv for $item_name activated."
    log_and_print "Installing dependencies..."
    for d in "${dependencies_array[@]}"; do
        log_and_print "Installing $d..."
        "$venv_dir_path"/bin/pip install "$d"
        if [ "$?" != "0" ]; then
            log_and_print "ERROR: Failed to install $d!"
            exit 1
        fi
        log_and_print "Installed $d."
    done
    deactivate && log_and_print "Deactivated venv." # exit venv
    log_and_print "Created Python venv for $item_name with dependencies."
    log_and_print "Moving $item_name code from $staging_dir_path to venv..."
    mv "$staging_dir_path" "$code_dir_path"
    log_and_print "Done with venv for $item_name."
}

# MARK: create_tarball()
function create_tarball(){
    tar -cvf "$PACKAGE_TARBALL" "$PACKAGE_ROOT_DIR"
    if [ "$?" != "0" ]; then
        log_and_print "ERROR: Failed to generate tarball: $PACKAGE_TARBALL"
        exit 1
    fi
    log_and_print "Created deployable tarball: $PACKAGE_TARBALL."
}

# MARK: log_and_print()
function log_and_print(){
    echo "    $1"
    if [ -f "$BUILD_LOG_PATH" ]; then
        echo "    $1" >> "$BUILD_LOG_PATH"
    fi
}

# MARK: log_and_print_header()
function log_and_print_header(){
    echo "===$1==="
    if [ -f "$BUILD_LOG_PATH" ]; then
        echo "===$1===" >> "$BUILD_LOG_PATH"
    fi
}

# MARK: main()
gather_info
pre_cleanup
log_and_print_header "CREATING INIT SCRIPT"
write_init_script
log_and_print_header "DOWNLOADING PYPY"
download_and_extract_pypy
log_and_print_header "CREATING VENV FOR MES"
create_venv "mes" "$MES_VENV_DIR" "$MES_STAGING_DIR" "$MES_CODE_DIR" MES_DEPENDENCIES[@]
log_and_print_header "GENERATING ARCHIVE"
create_tarball