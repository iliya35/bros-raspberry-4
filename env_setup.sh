#!/bin/bash

BR2_EXTERNAL="br_external"
BR2_DL_DIR="$BR2_EXTERNAL/downloads"
BR2_PATH="/usr/src/buildroot"
TARGET=""

function set_target() {
    if [ $# -ne 1 ]; then
        echo "Usage: set_target TARGET"
        return
    fi

    TARGET=$1
    echo "Set target: $TARGET"

    BULDROOT_OUTPUT="$BR2_EXTERNAL/output/$TARGET"
    m "${TARGET}_defconfig"
}

function get_target() {
    echo "Target: $TARGET"
}

function find_br2() {
    while [ "$PWD" != "/" ]; do
        case $CI in 
            true)
                if [ ! -f "$BR2_PATH/Makefile" ]; then
                    echo "Buildroot sources not found in:"
                    echo "$BR2_PATH"
                    return 1
                else 
                    echo "$BR2_PATH"
                    return
                fi
            ;;
            *)
                if [ -f "$PWD/buildroot/Makefile" ]; then
                    echo "$PWD/buildroot"
                    return
                elif [ ! -f "$BR2_PATH/Makefile" ]; then
                    echo "Buildroot sources not found in:"
                    echo "$BR2_PATH"
                    echo "$PWD/buildroot"
                    BR2_PATH=""
                else
                    echo "$BR2_PATH"
                    return
                fi
                cd ..
            ;;
        esac
    done
    echo "Error: could not buildroot path"
    return 1
}

function find_top() {
    while [ "$PWD" != "/" ]; do
        case $CI in 
            true)
                if [ -f "$CI_PROJECT_DIR/env_setup.sh" ]; then
                    echo "$CI_PROJECT_DIR/.."
                    return
                else
                    echo "BR2_EXTERNAL init script not found"
                    return 1
                fi
            ;;
            *)
                if [ -f "$BR2_EXTERNAL/env_setup.sh" ]; then
                    echo "$PWD"
                    return
                else
                    echo "BR2_EXTERNAL init script not found in:"
                    echo "$PWD"
                fi
                cd ..
            ;;
        esac
    done

    echo "Error: could not find top of the tree"
    return 1
}

function m() {
    local TOP
    TOP="$(find_top)" || return
    BR2_PATH="$(find_br2)" || return
    echo "Top dir: $TOP"
    if [ -z $TARGET ]; then
        echo "Error: need to set target"
        set_target
        return
    fi
    if [ -n "$CI" ]; then
        echo "Redefine varibles for CI:"
        BR2_EXTERNAL=$CI_PROJECT_NAME
        BR2_DL_DIR="$BR2_EXTERNAL/downloads"
        BULDROOT_OUTPUT="$BR2_EXTERNAL/output/$TARGET"
    fi

    echo "BR2_PATH=$BR2_PATH"
    echo "BR2_EXTERNAL=$BR2_EXTERNAL"
    echo "BR2_DL_DIR=$BR2_DL_DIR"
    echo "BULDROOT_OUTPUT=$BULDROOT_OUTPUT"

    make \
        BR2_EXTERNAL="$TOP/$BR2_EXTERNAL" \
        BR2_DL_DIR="$TOP/$BR2_DL_DIR" \
        O="$TOP/$BULDROOT_OUTPUT" \
        -C "$BR2_PATH" \
        -j$(nproc) \
        "$@"
}
