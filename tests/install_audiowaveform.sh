#!/bin/bash

# Quick and dirty AudioWaveform build with cache logic for speedup

if [ -z "$DRONE_RUNNER_PLATFORM" ]; then
    # CircleCI
    RUNNER="$(uname -s)-$(uname -r)"
    BINPATH="~/projects/audiowaveform/${RUNNER}/audiowaveform"
    CACHEPATH="~/projects/"
    CI="CircleCI"
else
    # Drone
    RUNNER=$DRONE_RUNNER_PLATFORM
    BINPATH="${PWD}/.cache/audiowaveform/${RUNNER}/audiowaveform"
    CACHEPATH="~/.cache"
    CI="DroneCI"
fi

# Build function
build() {
    echo "-- build audiowaveform; building AudioWaveform..."
    git clone https://github.com/bbcrd/audiowaveform.git /tmp/audiowaveform
    cd /tmp/audiowaveform
    wget https://github.com/google/googletest/archive/release-1.8.0.tar.gz -O gmock-1.8.0.tar.gz
    tar xzf gmock-1.8.0.tar.gz
    ln -s googletest-release-1.8.0/googletest googletest
    ln -s googletest-release-1.8.0/googlemock googlemock
    mkdir build
    cd build
    cmake ..
    make
    ${SUDO} mkdir -pv /usr/local/bin
    ${SUDO} cp -fv audiowaveform /usr/local/bin/audiowaveform
}

echo "-- CI detected: ${CI}"

# Cache logic : test if we have an executable already built, and working
if [[ -d $CACHEPATH ]]; then
    echo "-- build audiowaveform; cache available"
    # We have a cache dir, create struct
    mkdir -pv "${CACHEPATH}/audiowaveform/${RUNNER}"

    # Check if a binary exists
    if [[ -x ${BINPATH} ]]; then
        echo "-- build audiowaveform; binary exist"
        # Can we run it ?
        if ${BINPATH} --help|grep "AudioWaveform v"; then
            echo "-- build audiowaveform; and can run; copying it"
            # can run
            ${SUDO} cp -fv ${BINPATH} /usr/local/bin/audiowaveform
        else
            # can't run
            build
            cp -fv /usr/local/bin/audiowaveform ${BINPATH}
        fi
    else
        # Can't run it, build it
        build
        cp -fv /usr/local/bin/audiowaveform ${BINPATH}
    fi
else
    # No cache, build it
    build
    cp -fv /usr/local/bin/audiowaveform ${BINPATH}
fi
