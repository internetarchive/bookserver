#!/bin/bash


############ Setup of paths and packages ######################
#  to run on an alt. port/setup, change scripts.conf below in some petabox tree..
mydir=$(d=`dirname $0`; echo $d | grep '^/' || echo `pwd`/$d | perl -pe's=/\.$==')
CONF=$mydir/example/solr/conf/scripts.conf
# default /petabox/solr unless this script is being run from an alternate tree
SOLR_HOME=$mydir;
# default 8983 unless specific 2nd solr is running on alt port from an alt. tree
PORT=`egrep '^solr_port=[0-9]+' $CONF |tail -1|cut -f 2 -d =|tr -d '[:space:]'`;
# default /var/tmp/solr8983/data (unless alt tree specifies otherwise)
DATA_DIR=`egrep '^data_dir=/.+' $CONF |tail -1|cut -f 2 -d =|tr -d '[:space:]'`;
#
JAVA_HOME=/usr/lib/jvm/java-6-sun/jre
CLASSPATH="$JAVA_HOME/../lib/tools.jar"
RAM="-Xms2600m -Xmx2600m"
SOLR_TMP=`dirname $DATA_DIR`;
LOG=$SOLR_TMP/solr.log
USER=solr

export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
#export CLASSPATH="$CLASSPATH:$SOLR_HOME/example/lib/jsp-2.1/ant-1.6.5.jar:$SOLR_HOME/lib/junit-4.3.jar"
export CLASSPATH="$CLASSPATH:$SOLR_HOME/example/lib/jsp-2.1/ant-1.6.5.jar"
############ Setup of paths and packages ######################
echo; echo CONFIGURATON: [$SOLR_HOME][$PORT][$DATA_DIR][$SOLR_TMP][$LOG]; echo;




################################################################################
# Check if user corresponds to USER, otherwise rerun the script as USER
################################################################################
if [ `/usr/bin/whoami` != "$USER" ];then
    # squeak these off if we are root...
    ln -sf $SOLR_TMP/solr.log /var/log/solr.log

    # needed for the way we copy our SE updates to this dir
    #mkdir -p /var/tmp/solr/docs/xfer;

    # needed for replication
    mkdir -p                 $SOLR_HOME/example/solr/logs;
    chmod ug+rwX          -R $SOLR_HOME/example/solr/{logs,conf}/;
    chown solr -R $SOLR_HOME/example/solr/{logs,conf}/;

 
    touch $LOG
    chown solr $LOG
 
    echo "NOTE: You must be $USER to run -- sudo-ing now...";
    echo "NOTE: If prompted, enter your password for sudo to sudo $USER...";
    set -x
    sudo -u $USER $0 $*;
    set +x
    exit $?;
fi





#setup()
#{
#
#}

# FIXME/xxx wrong when starting 2nd solr on same box -- 2nd start kills 1st one.
# FIXME/xxx additionally, stops won't work while 2+ are running.
stop()
{
  if [ -d "/tmp/hsperfdata_$USER/" ]; then
    ret=`fgrep java /tmp/hsperfdata_$USER/* | fgrep 'Binary file' | fgrep 'matches' | grep -v grep | wc -l | tr -d ' '`
    if [ "$ret" == "1" ]; then
      lsnum=`/bin/ls /tmp/hsperfdata_$USER/ | wc -l | tr -d ' '`
      if [ "$lsnum" == "1" ]; then
        pid=`/bin/ls /tmp/hsperfdata_$USER/`

        # make sure this pid is *actually* running
        # (when server reboots, often /tmp is *not* cleaned, so can be "phantom"
        #  hsperfdata dir...)
        nrunning=`ps --no-headers -p $pid | wc -l | tr -d ' '`;

        if [ "$nrunning" != "0" ]; then
          kill -SIGINT $pid

          while true; do
            lsnum=`/bin/ls /tmp/hsperfdata_$USER/ | wc -l | tr -d ' '`
            if [ "$lsnum" == "0" ]; then
              break;
            fi
            echo "Waiting for server to stop..."
            sleep 2
          done
        fi
      fi
    fi
  fi
}

start()
{
  set +ex
  echo "Pausing 5 seconds to ensure we are not in constant crash loop under /etc/event.d/"
  /bin/sleep 5

#  set -ex
#  setup;
#  set +ex

#  cd $SOLR_HOME/example
#    if [ -f start.jar ]; then true; else
#    set -ex
#    setup;
#    set +ex
#  fi

  echo >> $LOG
  echo >> $LOG
  echo >> $LOG
  echo >> $LOG
  echo "------------Solr starting--"`date`"------"  >> $LOG
  date  >> $LOG
  date  >> $LOG


  cd $SOLR_HOME/example

  # for replication, start the solr rsync daemon...
  #set +e;
  #./solr/bin/snappuller-enable -v;
  #./solr/bin/rsyncd-enable -v;
  #./solr/bin/rsyncd-stop -u tracey;
  #( ./solr/bin/rsyncd-start -v -u tracey & wait );
  #set -e;


  set -ex
  # NOTE: keep min and max ram the same at startup for better performance
  java -Djetty.port=$PORT -Dsolr.data.dir=$DATA_DIR $RAM -jar start.jar >> $LOG 2>> $LOG
}


main()
{
  #correct-server;

  if   [ "$1" == "start"      ]; then
    set -ex;
    stop; start;
  elif [ "$1" == "start-only" ]; then
    set -ex;
    start;
  elif [ "$1" == "restart"    ]; then
    set -ex;
    stop; start;
  elif [ "$1" == "stop"       ]; then
    set -ex;
    stop;
  elif [ "$1" == "setup"      ]; then
    # forces setup to rerun
    set -ex;
    setup;
  fi;
}


if [ "$#" == "1" ]; then
  main $1;
else
  echo "Usage: $0 {start|start-only|stop|restart|setup}"
fi


