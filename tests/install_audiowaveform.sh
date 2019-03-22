#!/bin/sh

# Quick and dirty AudioWaveform build with cache logic for speedup

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
    mkdir -p /usr/local/bin
    cp audiowaveform /usr/local/bin/audiowaveform
}

BINPATH=".cache/audiowaveform/${DRONE_RUNNER_PLATFORM}/audiowaveform"

# Cache logic : test if we have an executable already built, and working
if [[ -d .cache ]]; then
    echo "-- build audiowaveform; cache available"
    # We have a cache dir, create struct
    mkdir -p .cache/audiowaveform/${DRONE_RUNNER_PLATFORM}

    # Check if a binary exists
    if [[ -x ${BINPATH} ]]; then
        echo "-- build audiowaveform; binary exist"
        # Can we run it ?
        if ${BINPATH}|grep "AudioWaveform v"; then
            echo "-- build audiowaveform; and can run; copying it"
            # can run
            cp -f ${BINPATH} /usr/local/bin/audiowaveform
        else
            # can't run
            build
        fi
    else
        # Can't run it, build it
        build
    fi
else
    # No cache, build it
    build
fi
