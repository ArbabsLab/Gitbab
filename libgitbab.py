import argparse
from datetime import datetime
from fnmatch import fnmatch
import os
import sys
from GitBab.GitbabObject import object_find, object_hash, object_read, tree_checkout
import GitbabRepo
        
parser = argparse.ArgumentParser(description="gitbab: git by Arbab")
subargparse = parser.add_subparsers(title="Args", dest="command")
subargparse.required = True
argsp = subargparse.add_parser("initbab", help="Initialize a new, empty gitbab repository.")
argsp.add_argument("path", metavar="directory", nargs="?", default=".", help="Where to create the repository.")
argsp = subargparse.add_parser("cat-file",
                                 help="Provide content of repository objects")

argsp.add_argument("type",
                   metavar="type",
                   choices=["blob", "commit", "tag", "tree"],
                   help="Specify the type")

argsp.add_argument("object",
                   metavar="object",
                   help="The object to display")

argsp = subargparse.add_parser(
    "hash-object",
    help="Compute object ID and optionally creates a blob from a file")

argsp.add_argument("-t",
                   metavar="type",
                   dest="type",
                   choices=["blob", "commit", "tag", "tree"],
                   default="blob",
                   help="Specify the type")

argsp.add_argument("-w",
                   dest="write",
                   action="store_true",
                   help="Actually write the object into the database")

argsp.add_argument("path",
                   help="Read object from <file>")

argsp = subargparse.add_parser("ls-tree", help="Pretty-print a tree object.")
argsp.add_argument("-r",
                   dest="recursive",
                   action="store_true",
                   help="Recurse into sub-trees")

argsp.add_argument("tree",
                   help="A tree-ish object.")

argsp = subargparse.add_parser("checkout", help="Checkout a commit inside of a directory.")

argsp.add_argument("commit",
                   help="The commit or tree to checkout.")

argsp.add_argument("path",
                   help="The EMPTY directory to checkout on.")

argsp = subargparse.add_parser("show-ref", help="List references.")

def main(argv=sys.argv[1:]):
    args = parser.parse_args(argv)
    cmd = args.command
    if cmd == "initbab":
        initbab(args)
    elif cmd == "addbab":
        addbab(args)
    elif cmd == "catbab-file":
        catbab(args)
    elif cmd == "checkout":
        checkoutbab(args)
    elif cmd == "commitbab":
        commitbab(args)
    elif cmd == "hashbab":
        hashbab(args)
    elif cmd == "logbab":
        logbab(args)
    elif cmd == "ls-treebab":
        ls_treebab(args)
    elif cmd == "show-refbab":
        show_refbab(args)
    

def initbab(args):
    GitbabRepo.repo_create(args.path)

def catbab(args):
    repo = GitbabRepo.repo_find()
    cat_file()

def hashbab(args):
    if args.write:
        repo = GitbabRepo.repo_find()
    else:
        repo = None

    with open(args.path, "rb") as fd:
        sha = object_hash(fd, args.type.encode(), repo)
        print(sha)

def logbab(args):
    repo = GitbabRepo.repo_find()

    print("digraph wyaglog{")
    print("  node[shape=rect]")
    log_graphviz(repo, object_find(repo, args.commit), set())
    print("}")
    
def ls_treebab(args):
    repo = GitbabRepo.repo_find()
    ls_treebab_helper(repo, args.tree, args.recursive)

def ls_treebab_helper(repo, ref, recursive=None, prefix=""):
    sha = object_find(repo, ref, fmt=b"tree")
    obj = object_read(repo, sha)
    for item in obj.items:
        if len(item.mode) == 5:
            type = item.mode[0:1]
        else:
            type = item.mode[0:2]

        match type:
            case b'04': type = "tree"
            case b'10': type = "blob"
            case b'12': type = "blob" 
            case b'16': type = "commit"
            case _: raise Exception("Weird tree leaf mode {}".format(item.mode))

        if not (recursive and type=='tree'):
            print("{0} {1} {2}\t{3}".format(
                "0" * (6 - len(item.mode)) + item.mode.decode("ascii"),
                type,
                item.sha,
                os.path.join(prefix, item.path)))
        else: 
            ls_treebab_helper(repo, item.sha, recursive, os.path.join(prefix, item.path))

def checkoutbab(args):
    repo = GitbabRepo.repo_find()

    obj = object_read(repo, object_find(repo, args.commit))

    if obj.fmt == b'commit':
        obj = object_read(repo, obj.kvlm[b'tree'].decode("ascii"))

    if os.path.exists(args.path):
        if not os.path.isdir(args.path):
            raise Exception("Not a directory {0}!".format(args.path))
        if os.listdir(args.path):
            raise Exception("Not empty {0}!".format(args.path))
    else:
        os.makedirs(args.path)

    tree_checkout(repo, obj, os.path.realpath(args.path))

def show_refbab(args):
    repo = GitbabRepo.repo_find()
    refs = GitbabRepo.ref_list(repo)
    show_ref(repo, refs, prefix="refs")

def show_ref(repo, refs, with_hash=True, prefix=""):
    for k, v in refs.items():
        if type(v) == str:
            print ("{0}{1}{2}".format(
                v + " " if with_hash else "",
                prefix + "/" if prefix else "",
                k))
        else:
            show_ref(repo, v, with_hash=with_hash, prefix="{0}{1}{2}".format(prefix, "/" if prefix else "", k))

def log_graphviz(repo, sha, seen):

    if sha in seen:
        return
    seen.add(sha)

    commit = object_read(repo, sha)
    short_hash = sha[0:8]
    message = commit.kvlm[None].decode("utf8").strip()
    message = message.replace("\\", "\\\\")
    message = message.replace("\"", "\\\"")

    if "\n" in message: 
        message = message[:message.index("\n")]

    print("  c_{0} [label=\"{1}: {2}\"]".format(sha, sha[0:7], message))
    assert commit.fmt==b'commit'

    if not b'parent' in commit.kvlm.keys():
        return

    parents = commit.kvlm[b'parent']

    if type(parents) != list:
        parents = [ parents ]

    for p in parents:
        p = p.decode("ascii")
        print ("  c_{0} -> c_{1};".format(sha, p))
        log_graphviz(repo, p, seen)

def cat_file(repo, obj, fmt=None):
    obj = object_read(repo, object_find(repo, obj, fmt=fmt))
    sys.stdout.buffer.write(obj.serialize())




    


