import argparse
import collections
import configparser
from datetime import datetime
from fnmatch import fnmatch
import grp
import os
import pwd
import sys
from GitBab.GitbabObject import GitCommit, GitIgnore, GitIndexEntry, GitTag, index_read, index_write, object_find, object_hash, object_read, object_write, tree_checkout, tree_from_index
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
    "hashbab",
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

argsp = subargparse.add_parser("ls-treebab", help="Pretty-print a tree object.")
argsp.add_argument("-r",
                   dest="recursive",
                   action="store_true",
                   help="Recurse into sub-trees")

argsp.add_argument("tree",
                   help="A tree-ish object.")

argsp = subargparse.add_parser("checkoutbab", help="Checkout a commit inside of a directory.")

argsp.add_argument("commitbab",
                   help="The commit or tree to checkout.")

argsp.add_argument("path",
                   help="The EMPTY directory to checkout on.")

argsp = subargparse.add_parser("show-refbab", help="List references.")

argsp = subargparse.add_parser(
    "tagbab",
    help="List and create tags")

argsp.add_argument("-a",
                   action="store_true",
                   dest="create_tag_object",
                   help="Whether to create a tag object")

argsp.add_argument("name",
                   nargs="?",
                   help="The new tag's name")

argsp.add_argument("object",
                   default="HEAD",
                   nargs="?",
                   help="The object the new tag will point to")

argsp = subargparse.add_parser(
    "rev-parsebab",
    help="Parse revision (or other objects) identifiers")

argsp.add_argument("--wyag-type",
                   metavar="type",
                   dest="type",
                   choices=["blob", "commit", "tag", "tree"],
                   default=None,
                   help="Specify the expected type")

argsp.add_argument("name",
                   help="The name to parse")

argsp = subargparse.add_parser("ls-filebab", help = "List all the stage files")
argsp.add_argument("--verbose", action="store_true", help="Show everything.")

argsp = subargparse.add_parser("check-ignorebab", help = "Check path(s) against ignore rules.")
argsp.add_argument("path", nargs="+", help="Paths to check")

argsp = subargparse.add_parser("statusbab", help = "Show the working tree status.")

argsp = subargparse.add_parser("rmbab", help="Remove files from the working tree and the index.")
argsp.add_argument("path", nargs="+", help="Files to remove")

argsp = subargparse.add_parser("addbab", help = "Add files contents to the index.")
argsp.add_argument("path", nargs="+", help="Files to add")

argsp = subargparse.add_parser("commitbab", help="Record changes to the repository.")

argsp.add_argument("-m",
                   metavar="message",
                   dest="message",
                   help="Message to associate with this commit.")

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
    elif cmd == "tagbab":
        tagbab(args)
    elif cmd == "rev-parsebab":
        rev_parsebab(args)
    elif cmd == "ls-filebab":
        ls_filebab(args)
    elif cmd == "check-ignorebab":
        check_ignorebab(args)
    elif cmd == "rmbab":
        rmbab(args)
    

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

def ls_filebab(args):
    repo = GitbabRepo.repo_find()
    index = index_read(repo)
    if args.verbose:
        print("Index file format v{}, containing {} entries.".format(index.version, len(index.entries)))

    for e in index.entries:
        print(e.name)
        if args.verbose:
            print("  {} with perms: {:o}".format(
                { 0b1000: "regular file",
                0b1010: "symlink",
                0b1110: "git link" }[e.mode_type],
                e.mode_perms))
            print("  on blob: {}".format(e.sha))
            print("  created: {}.{}, modified: {}.{}".format(
                datetime.fromtimestamp(e.ctime[0])
                , e.ctime[1]
                , datetime.fromtimestamp(e.mtime[0])
                , e.mtime[1]))
            print("  device: {}, inode: {}".format(e.dev, e.ino))
            print("  user: {} ({})  group: {} ({})".format(
                pwd.getpwuid(e.uid).pw_name,
                e.uid,
                grp.getgrgid(e.gid).gr_name,
                e.gid))
            print("  flags: stage={} assume_valid={}".format(
                e.flag_stage,
                e.flag_assume_valid))
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
def statusbab(args):
    repo = GitbabRepo.repo_find()
    index = index_read(repo)

    cmd_status_branch(repo)
    cmd_status_head_index(repo, index)
    print()
    cmd_status_index_worktree(repo, index)

def branch_get_active(repo):
    with open(GitbabRepo.repo_file(repo, "HEAD"), "r") as f:
        head = f.read()

    if head.startswith("ref: refs/heads/"):
        return(head[16:-1])
    else:
        return False

def cmd_status_branch(repo):
    branch = branch_get_active(repo)
    if branch:
        print("On branch {}.".format(branch))
    else:
        print("HEAD detached at {}".format (object_find(repo, "HEAD")))

def tree_to_dict(repo, ref, prefix=""):
  ret = dict()
  tree_sha = object_find(repo, ref, fmt=b"tree")
  tree = object_read(repo, tree_sha)

  for leaf in tree.items:
      full_path = os.path.join(prefix, leaf.path)

      is_subtree = leaf.mode.startswith(b'04')

      if is_subtree:
        ret.update(tree_to_dict(repo, leaf.sha, full_path))
      else:
        ret[full_path] = leaf.sha

  return ret

def cmd_status_head_index(repo, index):
    print("Changes to be committed:")

    head = tree_to_dict(repo, "HEAD")
    for entry in index.entries:
        if entry.name in head:
            if head[entry.name] != entry.sha:
                print("  modified:", entry.name)
            del head[entry.name] 
        else:
            print("  added:   ", entry.name)
    for entry in head.keys():
        print("  deleted: ", entry)

def cmd_status_index_worktree(repo, index):
    print("Changes not staged for commit:")

    ignore = gitignore_read(repo)

    gitdir_prefix = repo.gitdir + os.path.sep

    all_files = list()
    for (root, _, files) in os.walk(repo.worktree, True):
        if root==repo.gitdir or root.startswith(gitdir_prefix):
            continue
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, repo.worktree)
            all_files.append(rel_path)
    
    for entry in index.entries:
        full_path = os.path.join(repo.worktree, entry.name)


        if not os.path.exists(full_path):
            print("  deleted: ", entry.name)
        else:
            stat = os.stat(full_path)
            ctime_ns = entry.ctime[0] * 10**9 + entry.ctime[1]
            mtime_ns = entry.mtime[0] * 10**9 + entry.mtime[1]
            if (stat.st_ctime_ns != ctime_ns) or (stat.st_mtime_ns != mtime_ns):

                with open(full_path, "rb") as fd:
                    new_sha = object_hash(fd, b"blob", None)
                    same = entry.sha == new_sha

                    if not same:
                        print("  modified:", entry.name)

        if entry.name in all_files:
            all_files.remove(entry.name)

    print()
    print("Untracked files:")

    for f in all_files:
        # @TODO If a full directory is untracked, we should display
        # its name without its contents.
        if not check_ignore(ignore, f):
            print(" ", f)
def rmbab(args):
    repo = GitbabRepo.repo_find()
    rm(repo, args.path)

def rm(repo, paths, delete=True, skip_missing=False):
    index = index_read(repo)

    worktree = repo.worktree + os.sep

    abspaths = list()
    for path in paths:
        abspath = os.path.abspath(path)
        if abspath.startswith(worktree):
            abspaths.append(abspath)
        else:
            raise Exception("Cannot remove paths outside of worktree: {}".format(paths))

    kept_entries = list()

    remove = list()
    for e in index.entries:
        full_path = os.path.join(repo.worktree, e.name)

        if full_path in abspaths:
            remove.append(full_path)
            abspaths.remove(full_path)
        else:
            kept_entries.append(e) 

    if len(abspaths) > 0 and not skip_missing:
        raise Exception("Cannot remove paths not in the index: {}".format(abspaths))

    if delete:
        for path in remove:
            os.unlink(path)

    index.entries = kept_entries
    index_write(repo, index)

def addbab(args):
    repo = GitbabRepo.repo_find()
    add(repo, args.path)

def add(repo, paths, delete=True, skip_missing=False):
    rm (repo, paths, delete=False, skip_missing=True)

    worktree = repo.worktree + os.sep
    clean_paths = list()
    for path in paths:
        abspath = os.path.abspath(path)
        if not (abspath.startswith(worktree) and os.path.isfile(abspath)):
            raise Exception("Not a file, or outside the worktree: {}".format(paths))
        relpath = os.path.relpath(abspath, repo.worktree)
        clean_paths.append((abspath,  relpath))

        # Find and read the index.  It was modified by rm.  (This isn't
        # optimal, good enough for wyag!)
        #
        # @FIXME, though: we could just move the index through
        # commands instead of reading and writing it over again.
        index = index_read(repo)

        for (abspath, relpath) in clean_paths:
            with open(abspath, "rb") as fd:
                sha = object_hash(fd, b"blob", repo)

            stat = os.stat(abspath)

            ctime_s = int(stat.st_ctime)
            ctime_ns = stat.st_ctime_ns % 10**9
            mtime_s = int(stat.st_mtime)
            mtime_ns = stat.st_mtime_ns % 10**9

            entry = GitIndexEntry(ctime=(ctime_s, ctime_ns), mtime=(mtime_s, mtime_ns), dev=stat.st_dev, ino=stat.st_ino,
                                  mode_type=0b1000, mode_perms=0o644, uid=stat.st_uid, gid=stat.st_gid,
                                  fsize=stat.st_size, sha=sha, flag_assume_valid=False,
                                  flag_stage=False, name=relpath)
            index.entries.append(entry)

        index_write(repo, index)

def gitconfig_read():
    xdg_config_home = os.environ["XDG_CONFIG_HOME"] if "XDG_CONFIG_HOME" in os.environ else "~/.config"
    configfiles = [
        os.path.expanduser(os.path.join(xdg_config_home, "git/config")),
        os.path.expanduser("~/.gitconfig")
    ]

    config = configparser.ConfigParser()
    config.read(configfiles)
    return config

def gitconfig_user_get(config):
    if "user" in config:
        if "name" in config["user"] and "email" in config["user"]:
            return "{} <{}>".format(config["user"]["name"], config["user"]["email"])
    return None

def commit_create(repo, tree, parent, author, timestamp, message):
    commit = GitCommit() 
    commit.kvlm[b"tree"] = tree.encode("ascii")
    if parent:
        commit.kvlm[b"parent"] = parent.encode("ascii")

    offset = int(timestamp.astimezone().utcoffset().total_seconds())
    hours = offset // 3600
    minutes = (offset % 3600) // 60
    tz = "{}{:02}{:02}".format("+" if offset > 0 else "-", hours, minutes)

    author = author + timestamp.strftime(" %s ") + tz

    commit.kvlm[b"author"] = author.encode("utf8")
    commit.kvlm[b"committer"] = author.encode("utf8")
    commit.kvlm[None] = message.encode("utf8")

    return object_write(commit, repo)

def commitbab(args):
    repo = GitbabRepo.repo_find()
    index = index_read(repo)
    tree = tree_from_index(repo, index)
    commit = commit_create(repo,
                           tree,
                           object_find(repo, "HEAD"),
                           gitconfig_user_get(gitconfig_read()),
                           datetime.now(),
                           args.message)
    active_branch = branch_get_active(repo)
    if active_branch: 
        with open(GitbabRepo.repo_file(repo, os.path.join("refs/heads", active_branch)), "w") as fd:
            fd.write(commit + "\n")
        with open(GitbabRepo.repo_file(repo, "HEAD"), "w") as fd:
            fd.write("\n")
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

def rev_parsebab(args):
    if args.type:
        fmt = args.type.encode()
    else:
        fmt = None

    repo = GitbabRepo.repo_find()

    print (object_find(repo, args.name, fmt, follow=True))

def tagbab(args):
    repo = GitbabRepo.repo_find()

    if args.name:
        tag_create(repo,
                   args.name,
                   args.object,
                   type="object" if args.create_tag_object else "ref")
    else:
        refs = GitbabRepo.ref_list(repo)
        show_ref(repo, refs["tags"], with_hash=False)

def check_ignorebab(args):
    repo = GitbabRepo.repo_find()
    rules = gitignore_read(repo)
    for path in args.path:
        if check_ignore(rules, path):
            print(path)
def tag_create(repo, name, ref, create_tag_object=False):
    sha = object_find(repo, ref)

    if create_tag_object:
 
        tag = GitTag(repo)
        tag.kvlm = collections.OrderedDict()
        tag.kvlm[b'object'] = sha.encode()
        tag.kvlm[b'type'] = b'commit'
        tag.kvlm[b'tag'] = name.encode()
        tag.kvlm[b'tagger'] = b'gitbab <gitbab@example.com>'
        tag.kvlm[None] = b"A tag generated by gitbab"
        tag_sha = object_write(tag)
        ref_create(repo, "tags/" + name, tag_sha)
    else:
        
        ref_create(repo, "tags/" + name, sha)

def ref_create(repo, ref_name, sha):
    with open(GitbabRepo.repo_file(repo, "refs/" + ref_name), 'w') as fp:
        fp.write(sha + "\n")

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

def gitignore_parse1(raw):
    raw = raw.strip()

    if not raw or raw[0] == "#":
        return None
    elif raw[0] == "!":
        return (raw[1:], False)
    elif raw[0] == "\\":
        return (raw[1:], True)
    else:
        return (raw, True)

def gitignore_parse(lines):
    ret = list()

    for line in lines:
        parsed = gitignore_parse1(line)
        if parsed:
            ret.append(parsed)

    return ret

def gitignore_read(repo):
    ret = GitIgnore(absolute=list(), scoped=dict())

    repo_file = os.path.join(repo.gitdir, "info/exclude")
    if os.path.exists(repo_file):
        with open(repo_file, "r") as f:
            ret.absolute.append(gitignore_parse(f.readlines()))

    if "XDG_CONFIG_HOME" in os.environ:
        config_home = os.environ["XDG_CONFIG_HOME"]
    else:
        config_home = os.path.expanduser("~/.config")
    global_file = os.path.join(config_home, "git/ignore")

    if os.path.exists(global_file):
        with open(global_file, "r") as f:
            ret.absolute.append(gitignore_parse(f.readlines()))

    index = index_read(repo)

    for entry in index.entries:
        if entry.name == ".gitignore" or entry.name.endswith("/.gitignore"):
            dir_name = os.path.dirname(entry.name)
            contents = object_read(repo, entry.sha)
            lines = contents.blobdata.decode("utf8").splitlines()
            ret.scoped[dir_name] = gitignore_parse(lines)
    return ret

def check_ignore1(rules, path):
    result = None
    for (pattern, value) in rules:
        if fnmatch(path, pattern):
            result = value
    return result

def check_ignore_scoped(rules, path):
    parent = os.path.dirname(path)
    while True:
        if parent in rules:
            result = check_ignore1(rules[parent], path)
            if result != None:
                return result
        if parent == "":
            break
        parent = os.path.dirname(parent)
    return None

def check_ignore_absolute(rules, path):
    parent = os.path.dirname(path)
    for ruleset in rules:
        result = check_ignore1(ruleset, path)
        if result != None:
            return result
    return False

def check_ignore(rules, path):
    if os.path.isabs(path):
        raise Exception("This function requires path to be relative to the repository's root")

    result = check_ignore_scoped(rules.scoped, path)
    if result != None:
        return result

    return check_ignore_absolute(rules.absolute, path)
    


