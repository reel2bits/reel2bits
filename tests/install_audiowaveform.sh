#!/bin/sh
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
