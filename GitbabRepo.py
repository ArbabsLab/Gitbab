import os
import configparser
import argparse
import collections
from datetime import datetime
import grp, pwd
from fnmatch import fnmatch
import hashlib
import sys
import re
import zlib

class GitbabRepository(object):
    worktree = None
    gitdir = None
    conf = None

    def __init__(self, path, force=False):
        self.worktree = path
        self.gitdir = os.path.join(path, ".git")

        if not (force or os.path.isdir(self.gitdir)):
            raise Exception(f"Not a gitbab repo: {path}")
        
        self.conf = configparser.ConfigParser()
        cf = repo_file(self, "config")

        if cf and os.path.exists(cf):
            self.conf.read([cf])
        elif not force:
            raise Exception("Config file missing")
        
        def repo_path(repo, *path):
            return os.path.join(repo.gitdir, *path)
            
        def repo_file(repo, *path, mkdir=False):
            if repo_directory(repo, *path, mkdir=False):
                return repo_path(repo, *path)
            
        def repo_directory(repo, *path, mkdir=False):
            path = repo_path(repo, *path)

            if os.path.exists(path):
                if (os.path.isdir(path)):
                    return path
                else:
                    raise Exception(f"Not a directory {path}")
                
            if mkdir:
                os.makedirs(path)
                return path
            else:
                return None
            
        def repo_create(path):
            repo = GitbabRepository(path, True)
            if os.path.exists(repo.worktree):
                if not os.path.isdir(repo.worktree):
                    raise Exception (f"{path} is not a directory!")
                if os.path.exists(repo.gitdir) and os.listdir(repo.gitdir):
                    raise Exception(f"{path} is not empty!")
            else:
                os.makedirs(repo.worktree)

            assert repo_directory(repo, "branches", mkdir=True)
            assert repo_directory(repo, "objects", mkdir=True)
            assert repo_directory(repo, "refs", "tags", mkdir=True)
            assert repo_directory(repo, "refs", "heads", mkdir=True)

            with open(repo_file(repo, "description"), "w") as f:
                f.write("Unnamed repository; edit this file 'description' to name the repository.\n")

            with open(repo_file(repo, "HEAD"), "w") as f:
                f.write("ref: refs/heads/master\n")

            with open(repo_file(repo, "config"), "w") as f:
                config = repo_default_config()
                config.write(f)

            return repo
        
        def repo_default_config():
            ret = configparser.ConfigParser()

            ret.add_section("core")
            ret.set("core", "repositoryformatversion", "0")
            ret.set("core", "filemode", "false")
            ret.set("core", "bare", "false")

            return ret        
        