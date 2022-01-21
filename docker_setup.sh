DOCKER_BUILDROOT_VER=$(git ls-remote --sort='version:refname' \
                    --tags --refs https://github.com/buildroot/buildroot.git '2021.02.*' \
                    | tail --lines=1 | cut --delimiter='/' --fields=3)
DOCKER_USER=buildroot
DOCKER_IMAGE="buildroot:$DOCKER_BUILDROOT_VER"
HOST_SRC="$(pwd)"
SCRIPT_PATH="`dirname \"$0\"`"

echo "Target BuildRoot version: buildroot:$DOCKER_BUILDROOT_VER"

docker_build() {
    docker build \
        -t $DOCKER_IMAGE \
        -f "$SCRIPT_PATH/Dockerfile" \
        --build-arg UID=$(id -u) \
        --build-arg GID=$(id -g) \
        --build-arg UNAME=$DOCKER_USER \
        --build-arg BUILDROOT_VER=$DOCKER_BUILDROOT_VER \
        .
    read -p "Do you want push the $DOCKER_IMAGE image to local registy server ssrs.local:5000? [Y/n] " -n 1 -r
    echo    # (optional) move to a new line
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        TARGET_TAG="ssrs.local:5000/buildroot:latest"
        docker tag $DOCKER_IMAGE $TARGET_TAG
        docker push $TARGET_TAG
    fi
}

docker_run() {
    docker run \
        -ti --rm \
        -v $HOST_SRC:/home/$DOCKER_USER/src \
        $DOCKER_IMAGE \
        bash
}

case $1 in
    "build" ) docker_build ;;
    "run" ) docker_run ;;
esac