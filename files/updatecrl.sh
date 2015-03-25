#!/bin/bash

URL=https://admin.fedoraproject.org/ca/crl.pem
OLD=/etc/pki/tls/crl.pem
NEW=/tmp/crl.pem

if [ -f $OLD ]; then
    wget -q $URL -O $NEW
    OLDUPDATE=`openssl crl -in $OLD -noout -lastupdate`
    NEWUPDATE=`openssl crl -in $NEW -noout -lastupdate`

    if [ "$OLDUPDATE" != "$NEWUPDATE" ]; then
        mv $NEW $OLD
        /usr/sbin/restorecon $OLD
        /usr/bin/systemctl reload httpd
    fi
else
    wget -q $URL -O  $OLD
    /usr/sbin/restorecon $OLD
    /usr/bin/systemctl is-active httpd && /usr/bin/systemctl reload httpd
fi
