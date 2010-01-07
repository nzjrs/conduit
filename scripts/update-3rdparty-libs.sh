#!/bin/sh

APP="conduit/conduit"
if [ ! -f $APP ] ; then
    echo "ERROR: Must be run from top directory"
    exit 1
fi

#update pyfacebook
echo "Updating pyfacebook"
wget -qO conduit/modules/FacebookModule/pyfacebook/__init__.py http://github.com/sciyoshi/pyfacebook/raw/master/facebook/__init__.py

#update pybackpack
echo "Updating pybackpack"
for i in COPYING backpack.py; do
    echo "    ...downloading $i"
    wget -qO conduit/modules/BackpackModule/backpack/${i} http://github.com/dustin/py-backpack/raw/master/${i}
done

#update pyrtm
echo "Updating pyrtm"
wget -qO conduit/modules/UNSUPPORTED/RTMModule/rtm.py http://bitbucket.org/srid/pyrtm/raw/f4715bfbcffa/rtm.py


