#!/bin/sh
if [ "$spam" = "ON" ]; then
    DIR=/home/$username/.spamassassin
    mkdir $DIR
    touch $DIR/user_prefs     #or this is where you'd copy the default user_prefs you want them to have, instead of "touch".
    chown ${username}:mail $DIR
    chmod 771 $DIR
    chown $username:$username $DIR/user_prefs
    chmod 755 $DIR/user_prefs
    touch $DIR/spam
    chown mail:$username $DIR/spam
    chmod 660 $DIR/spam
fi

