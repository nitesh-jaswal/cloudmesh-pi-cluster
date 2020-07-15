import os
import subprocess
import shutil

from cloudmesh.common.parameter import Parameter
from cloudmesh.common.console import Console
from cloudmesh.common.util import readfile
from cloudmesh.common.util import writefile
from cloudmesh.common.Host import Host
from cloudmesh.common.JobSet import JobSet
import platform
import sys
from cloudmesh.common.util import banner
from pprint import pprint
import textwrap
from cloudmesh.common.Tabulate import Printer

class Mongo:

    def execute(self, arguments):
        """
        pi mongo install [--master=MASTER] [--workers=WORKERS]
        pi mongo start [--type=LOCAL/REPLICA] [--master=MASTER] [--port=PORT] [--dbpath=DBPATH]
        pi mongo stop
        pi mongo test --master=MASTER
        pi mongo uninstall --master=MASTER [--workers=WORKERS]

        :param arguments:
        :return:
        """
        self.master = arguments.master
        self.workers = Parameter.expand(arguments.workers)

        master = []
        hosts = []
        if arguments.master:
            hosts.append(arguments.master)

        if arguments.workers:
            hosts = hosts + Parameter.expand(arguments.workers)

        if arguments.dryrun:
            self.dryrun = True

        if (hosts is None) and (arguments.stop is None):
           Console.error("You need to specify at least one master or worker")
           return

        if arguments.install:
            self.install(hosts)

        elif arguments.start:
            if(arguments.type is "local"):
                self.start_local(arguments.port, arguments.dbpath)
            elif(arguments.type is "replica"):
                self.start_replica()

        elif arguments.stop:
            self.stop()
        elif arguments.test:
            print("Test Mongo")
            # self.test(master)
            #self.run_script(name="spark.test", hosts=self.master)
            
        elif arguments.uninstall:
            self.uninstall(hosts)

    def install(self, hosts):

        job_set = JobSet("mongo_install", executor=JobSet.ssh)
        command = """
            sudo apt update
            sudo apt -y upgrade
            sudo apt -y install mongodb
            sudo apt-get -y install python3-pip
            python3 -m pip install pymongo
            mkdir ~/data
            cd ~/data
            mkdir db
            """

        for host in hosts:
            # if self.is_installed(host) is False:
            job_set.add({"name": host, "host": host, "command": command})

        job_set.run(parallel=len(hosts))
        job_set.Print()
        banner("MongoDB Setup Complete")

    def uninstall(self, hosts):
        #             rm -rf ~/data/db
        job_set = JobSet("mongo_install", executor=JobSet.ssh)
        command = """
            sudo apt-get -y remove mongodb
            sudo apt-get -y remove --purge mongodb
            sudo apt-get autoremove
            python3 -m pip uninstall pymongo
            """

        for host in hosts:
            # if self.is_installed(host) is False:
            job_set.add({"name": host, "host": host, "command": command})

        job_set.run(parallel=len(hosts))
        job_set.Print()
        banner("MongoDB Removed Succesfully")
        return


    def start_local(self, port, dbpath):
    	# Error: Not starting. Need to check
        if port is None:
            port=27014
        elif dbpath is None:
            dbpath="/data/db"
        command = f"mongod --dbpath={dbpath} --port={port}"
        subprocess.run(command, shell=False, capture_output=False)

    def start_replica(self):
        Console.msg("Replica")

    def stop(self):
        command = "sudo service mongodb stop"
        subprocess.run(command.split(" "), shell=False, capture_output=False)
        banner("MongoDB service stopped succesfully")
        return

    #### CHANGE SO THAT os.shutil runs on the ssh of the host being probed #### 
    # def is_installed(self, host):
    #     '''
    #     Checks if there is a preexisting mongo installation on the host
    #     '''
    #     Console.msg(f"Checking for an existing mongo installation on {host} ")
    #     if (shutil.which("mongo") or shutil.which("mongod")) is None:
    #         Console.msg("Mongo installation not found.\n Installing MongoDB...")
    #         return False
    #     else:
    #         output = subprocess.check_output('mongo --version', shell=True)
    #         Console.error(f"Existing mongo installation found on {host}\n{output.decode('utf-8')}")
    #         return True
