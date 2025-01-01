import collections
import hashlib
import os
import zlib

from GitBab.GitbabRepo import repo_file

class GitbabObject(object):
    def __init__(self, data=None):
        if data != None:
            self.deserialize(data)
        else:
            self.init()
    
    def serialize(self, repo):
        raise Exception("Unimplemented")
    
    def deserialize(self, data):
        raise Exception("Unimplemented")
    
    def init(self):
        pass

class GitBlob(GitbabObject):
    fmt=b'blob'

    def serialize(self):
        return self.blobdata

    def deserialize(self, data):
        self.blobdata = data

class GitCommit(GitbabObject):
    fmt=b'commit'

    def deserialize(self, data):
        self.kvlm = kvlm_parse(data)

    def serialize(self):
        return kvlm_serialize(self.kvlm)

    def init(self):
        self.kvlm = dict()

class GitTree(GitbabObject):
    fmt=b'tree'

    def deserialize(self, data):
        self.items = tree_parse(data)

    def serialize(self):
        return tree_serialize(self)

    def init(self):
        self.items = list()

class GitTreeLeaf (object):
    def __init__(self, mode, path, sha):
        self.mode = mode
        self.path = path
        self.sha = sha

class GitTag(GitCommit):
    fmt = b'tag'

def tree_parse_one(raw, start=0):
    x = raw.find(b' ', start)
    assert x-start == 5 or x-start==6

    mode = raw[start:x]
    if len(mode) == 5:
        mode = b" " + mode
    y = raw.find(b'\x00', x)
    path = raw[x+1:y]

    raw_sha = int.from_bytes(raw[y+1:y+21], "big")
    sha = format(raw_sha, "040x")
    return y+21, GitTreeLeaf(mode, path.decode("utf8"), sha)

def tree_parse(raw):
    pos = 0
    max = len(raw)
    ret = list()
    while pos < max:
        pos, data = tree_parse_one(raw, pos)
        ret.append(data)

    return ret

def tree_leaf_sort_key(leaf):
    if leaf.mode.startswith(b"10"):
        return leaf.path
    else:
        return leaf.path + "/"

def tree_serialize(obj):
    obj.items.sort(key=tree_leaf_sort_key)
    ret = b''
    for i in obj.items:
        ret += i.mode
        ret += b' '
        ret += i.path.encode("utf8")
        ret += b'\x00'
        sha = int(i.sha, 16)
        ret += sha.to_bytes(20, byteorder="big")
    return ret

def tree_checkout(repo, tree, path):
    for item in tree.items:
        obj = object_read(repo, item.sha)
        dest = os.path.join(path, item.path)

        if obj.fmt == b'tree':
            os.mkdir(dest)
            tree_checkout(repo, obj, dest)
        elif obj.fmt == b'blob':
            # @TODO Support symlinks (identified by mode 12****)
            with open(dest, 'wb') as f:
                f.write(obj.blobdata)

def kvlm_serialize(kvlm):
    ret = b''

    for k in kvlm.keys():
        if k == None: continue
        val = kvlm[k]
        if type(val) != list:
            val = [ val ]

        for v in val:
            ret += k + b' ' + (v.replace(b'\n', b'\n ')) + b'\n'

    ret += b'\n' + kvlm[None] + b'\n'

    return ret

def kvlm_parse(raw, start=0, dct=None):
    # Key-Value List with Message
    if not dct:
        dct = collections.OrderedDict()

    spc = raw.find(b' ', start)  # space
    nl = raw.find(b'\n', start)  # new line

    # if space appers before newline, there is a keyword

    # basecase
    # if newline appers first (or there is no space at all, in which case return -1), there is a blank line. A blank line means the remainder of the data is message.
    if spc < 0 or nl < spc:
        assert(nl == start)
        dct[b''] = raw[start+1:]  # '': message...
        return dct

    # read keyword
    key = raw[start:spc]

    # find the end of the value
    end = start
    while True:
        end = raw.find(b'\n', end + 1)
        if raw[end + 1] != ord(' '):
            break

    # read value
    value = raw[spc+1:end].replace(b'\n', b'\n')

    if key in dct:  # do not overwrite the existing data
        if type(dct[key]) == list:
            dct[key].append(value)
        else:
            dct[key] = [dct[key], value]
    else:
        dct[key] = value

    return kvlm_parse(raw, start=end+1, dct=dct)

def object_read(repo, sha):
    path = repo_file(repo, "objects", sha[:2], sha[2:])

    if not os.path.isfile(path):
        return None
    with open (path, "rb") as f:
        raw = zlib.decompress(f.read())
        x = raw.find(b' ')
        fmt = raw[0:x]

        y = raw.find(b'\x00', x)
        size = int(raw[x:y].decode("ascii"))
        if size != len(raw)-y-1:
            raise Exception("Malformed object {0}: bad length".format(sha))
        
        if fmt == b'commit':
            c = GitbabCommit
        elif fmt == b'tree':
            c = GitbabTree
        elif fmt == b'tag':
            c = GitbabTag
        elif fmt == b'blob':
            c = GitbabBlob
        else:
            raise Exception("Unknown type {} for object {}".format(
                fmt.decode("ascii"), sha))

        return c(repo, raw[y+1:])

def object_write(obj, repo=None): 
    data = obj.serialize()
    result = obj.fmt + b' ' + str(len(data)).encode() + b'\x00' + data
    sha = hashlib.sha1(result).hexdigest()

    if repo:
        path=repo_file(repo, "objects", sha[0:2], sha[2:], mkdir=True)

        if not os.path.exists(path):
            with open(path, 'wb') as f:
                f.write(zlib.compress(result))
    return sha

def object_find(repo, name, fmt=None, follow=True):
    return name

def object_hash(f, fmt, repo=None):
    data = f.read()

    if fmt == b'commit':
        obj = GitCommit(data)
    elif fmt == b'tree':
        obj = GitTree(data)
    elif fmt == b'tag':
        obj = GitTag(data)
    elif fmt == b'blob':
        obj = GitBlob(data)
    else:
        raise Exception("Unknown type {}".format(fmt))

    return object_write(obj, repo)