#!/bin/sh

# BEFORE USING:
# This updates the code by retrieving the master branch download link, which is usually in the archive.
# A backup is stored with the name ${CODE_DIR}_old.
# Hopefully the sh command is stored at /bin/sh.
# Should restart the terminal after usage, or some shell glitchiness might occur due to the moving around.

# The name of the unzipped master branch folder
UNZIP_NAME=Reptile-Misters-master

# The name of the 'home directory', AKA parent directory of code directory
HOME_DIR=/home/pi

# The name of the code directory itself.
CODE_DIR=Zoo

cd $HOME_DIR/$CODE_DIR
wget -O ./master.zip https://github.com/jdutro86/Reptile-Misters/archive/master$
tar -xf ./master.zip
rm ./master.zip
mv ../$CODE_DIR ../${CODE_DIR}_old
mkdir ../$CODE_DIR
mv ./$UNZIP_NAME/* ../$CODE_DIR
rm -r ./$UNZIP_NAME
