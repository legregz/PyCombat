    #!/usr/bin/env bash
    set -e
    BASE_IMAGE="nayzbysodium/gregserv"
    REGISTRY="registry.hub.docker.com"
    IMAGE="$REGISTRY/$BASE_IMAGE"
    CID=$(docker ps | grep $IMAGE | awk '{print $1}')
    docker pull $IMAGE

    for im in $CID
    do
        LATEST=`docker inspect --format "{{.Id}}" $IMAGE`
        RUNNING=`docker inspect --format "{{.Image}}" $im`
        NAME=`docker inspect --format '{{.Name}}' $im | sed "s/\///g"`
        echo "Latest:" $LATEST
        echo "Running:" $RUNNING
        if [ "$RUNNING" != "$LATEST" ];then
            echo "upgrading $NAME"
            stop docker-$NAME
            docker rm -f $NAME
            start docker-$NAME
        else
            echo "$NAME up to date"
        fi
    done
