import argparse
import collections
import configparser
from datetime import datetime
import grp, pwd
from fnmatch import fnmatch
import hashlib
import os
import sys
import re
import zlib

parser = argparse.ArgumentParser(description="gitbab: git by Arbab")
subargparse = parser.add_subparsers(title="Args", dest="command")
subargparse.required = True

def main(argv=sys.argv[1:]):
    args = subargparse.parse_args(argv)
    cmd = args.command
    if cmd == "initbab":
        initbab(args)
    elif cmd == "addbab":
        addbab(args)
    elif cmd == "catbab-file":
        catbab(args)
    elif cmd == "commitbab":
        commitbab(args)
    elif cmd == "hashbab":
        hashbab(args)
    elif cmd == "catbab-file":
        catbab(args)
    elif cmd == "catbab-file":
        catbab(args)
    elif cmd == "catbab-file":
        catbab(args)
    


