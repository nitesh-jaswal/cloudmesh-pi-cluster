import os
import textwrap
from pprint import pprint

from cloudmesh.pi.cluster.Installer import Installer
from cloudmesh.pi.cluster.Installer import Script
from cloudmesh.common.Host import Host
from cloudmesh.common.Printer import Printer
from cloudmesh.common.console import Console
from cloudmesh.common.parameter import Parameter
from cloudmesh.common.util import banner

class Spark:

    def execute(self, arguments):
        """
        pi spark worker add [--master=MASTER] [--workers=WORKERS] [--dryrun]
        pi spark worker remove [--master=MASTER] [--workers=WORKERS] [--dryrun]
        pi spark setup [--master=MASTER] [--workers=WORKERS] [--dryrun]
        pi spark start [--master=MASTER] [--workers=WORKERS] [--dryrun]
        pi spark stop [--master=MASTER] [--workers=WORKERS] [--dryrun]
        pi spark test [--master=MASTER] [--workers=WORKERS] [--dryrun]
        pi spark check [--master=MASTER] [--workers=WORKERS] [--dryrun]

        :param arguments:
        :return:
        """
        self.master = arguments.master
        self.workers = Parameter.expand(arguments.workers)

        hosts = []
        if arguments.master:
            hosts.append(arguments.master)
        if arguments.workers:
            hosts = hosts + Parameter.expand(arguments.workers)

        if hosts is None:
            Console.error("You need to specify at least one master or worker")
            return ""

        if arguments.setup:

            self.run_script(name="spark.setup", hosts=hosts)

        elif arguments.start:

            self.run_script(name="spark.start", hosts=hosts)

        elif arguments.stop:

            self.run_script(name="spark.stop", hosts=hosts)

        elif arguments.test:

            self.run_script(name="spark.test", hosts=hosts)

        elif arguments.check:

            self.run_script(name="spark.check", hosts=hosts)

    def __init__(self, master=None, workers=None):
        """

        :param master:
        :param workers:
        """
        self.master = master
        self.workers = workers
        self.script = Script()
        self.service = "spark"
        self.java_version = "11"
        self.version = "2.4.5"
        self.user = "pi"
        self.scripts()

    def run(self,
            script=None,
            hosts=None,
            username=None,
            processors=4,
            verbose=False):

        results = []

        if type(hosts) != list:
            hosts = Parameter.expand(hosts)

        hostname = os.uname()[1]
        for command in script.splitlines():
            print (hosts, "->", command)
            if command.startswith("#") or command.strip() == "":
                pass
                # print (command)
            elif len(hosts) == 1 and hosts[0] == hostname:
                os.system(command)
            elif len(hosts) == 1 and hosts[0] != hostname:
                host = hosts[0]
                os.system(f"ssh {host} {command}")
            else:
                result = Host.ssh(hosts=hosts,
                                  command=command,
                                  username=username,
                                  key="~/.ssh/id_rsa.pub",
                                  processors=processors,
                                  executor=os.system)
                results.append(result)
        if verbose:
            pprint(results)
            for result in results:
                print(Printer.write(result, order=['host', 'stdout']))
        return results

    def scripts(self):

        version = "2.4.5"

        self.script["spark.check"] = """
            hostname
            uname -a
        """

        self.script["spark.test"] = """
            sh $SPARK_HOME/sbin/start-all.sh
            $SPARK_HOME/bin/run-example SparkPi 4 10
            sh $SPARK_HOME/sbin/stop-all.sh
        """

        self.script["spark.setup.master"] = """
               sudo apt-get update
               sudo apt-get install default-jdk
               sudo apt-get install scala
               cd ~
               sudo wget http://mirror.metrocast.net/apache/spark/spark-{version}/spark-{version}-bin-hadoop2.7.tgz -O sparkout.tgz
               sudo tar -xzf sparkout.tgz
               sudo cp ~/.bashrc ~/.bashrc-backup
        """

        self.script["spark.update.bashrc"] = """
                #JAVA_HOME
                export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-armhf/
                #SCALA_HOME
                export SCALA_HOME=/usr/share/scala
                export PATH=$PATH:$SCALA_HOME/bin
                #SPARK_HOME
                export SPARK_HOME=~/spark-2.4.5-bin-hadoop2.7
                export PATH=$PATH:$SPARK_HOME/bin
        """

        self.script["spark.start"] = """
            cat $SPARK_HOME/conf/slaves
            sh $SPARK_HOME/sbin/start-all.sh
        """

        self.script["spark.stop"] = """
            cat $SPARK_HOME/conf/slaves
            sh $SPARK_HOME/sbin/stop-all.sh
        """

        self.script["spark.setup.worker"] = """
             sudo apt-get update
             sudo apt-get install default-jdk
             sudo apt-get install scala
             cd ~
             sudo tar -xzf sparkout.tgz
             sudo cp ~/.bashrc ~/.bashrc-backup
         """

        self.script["copy.spark.to.worker"] = """
               scp /bin/spark-setup-worker.sh pi@self.workers:
               scp ~/sparkout.tgz pi@self.workers:
               ssh pi@self.workers sh ~/spark-setup-worker.sh
        """

        self.script["copy.spark.to.worker"] = """
               scp /bin/spark-setup-worker.sh pi@self.workers:
               scp ~/sparkout.tgz pi@self.workers:
               ssh pi@self.workers sh ~/spark-setup-worker.sh
        """


        # self.script["spark.uninstall2.4.5"] = """
        #     sudo apt-get remove openjdk-11-jre
        #     sudo apt-get remove scala
        #     cd ~
        #     sudo rm -rf spark-2.4.5-bin-hadoop2.7
        #     sudo rm -f sparkout.tgz
        #     sudo cp ~/.bashrc-backup ~/.bashrc
        # """

        return self.script

    def run_script(self, name=None, hosts=None):
        banner(name)
        results = self.run(script=self.script[name], hosts=hosts, verbose=True)

    def setup(self, arguments):
        """

        :return:
        """
        #
        # SETUP MASTER
        #
        if self.master:
            self.run_script(name="spark.setup.master", hosts=self.master)
            # self.update_bashrc(self)
            # self.spark_env(self)
        #
        # SETUP WORKER
        #
        if self.workers:
            self.create_spark.setup.worker(self)
            self.create_spark-bashrc.txt(self)
            self.run_script(name="copy.spark.to.worker", hosts=self.workers)
            self.update_slaves(self)
        raise NotImplementedError
    #
    #     # Setup Pi workflow
    #     # Setup the Pi master with the Spark applications
    #       script "spark.setup.master"
    #
    #     # Update the Pi master's ~/.bashrc file
    #       function update_bashrc(self)
    #
    #     # Create a shell file on Pi master to run on Pi worker
    #       function create_spark_setup_worker(self)
    #
    #     # Create a file on Pi master that will be copied to and append to ~/.bashrc on Pi worker
    #       function create_spark_bashrc_txt
    #
    #     # Copy shell and bashrc change files to Pi workers, execute shell file on Pi worker
    #       script "copy.spark.to.worker"
    #
    #     # Update slaves file on master
    #       function update_slaves(self)

    def test(self):
        if self.master:
            self.run_script(name="spark.test", hosts=self.master)
        raise NotImplementedError

    def update_slaves(self):
        """
        Add new worker name to bottom of slaves file on master
        :return:
        """
        if self.master:
            banner("Updating $SPARK_HOME/conf/slaves file")
            script = "pi@self.master"
            print(script)
            Installer.add_script("$SPARK_HOME/conf/slaves", script)
        raise NotImplementedError

    def update_bashrc(self):
        """
        Add the following lines to the bottom of the ~/.bashrc file
        :return:
        """
        banner("Updating ~/.bashrc file")
        script = textwrap.dedent(self.script["spark.update.bashrc"])
        Installer.add_script("/home/pi/.bashrc", script)

    def create_spark_setup_worker(self):
        """
        This file is created on master and copied to worker, then executed on worker from master
        :return:
        """
        banner("Creating the spark.setup.worker.sh file")
        script = self.script["spark.setup.worker.sh"]

        if self.dryrun:
            print(script)
        else:
            f = open("/home/pi/spark-setup-worker.sh", "w+")
            # f.write("test")
            f.close()
            Installer.add_script("~/spark-setup-worker.sh", script)

    def create_spark_bashrc_txt(self):
        """
        Test to add at bottome of ~/.bashrc.  File is created on master and copied to worker
        :return:
        """
        script = self.script["update.bashrc"]

        if self.dryrun:
            print(script)
        else:
            f = open("/home/pi/spark-bashrc.txt", "w+")
            # f.write("test")
            f.close()
            Installer.add_script("~/spark-bashrc.txt", script)
