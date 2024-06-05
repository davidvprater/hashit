# hashit
Hashing script in Python to store and check file hashes, typically for duplicate checking.

It does a very simple SHA256 hash, which is less prone to collision than MD5.  I understand collisions are still possible, but they'd be very rare.

It creates an SQLite database file per collection in your home directory under .hashes/ 

**Note:** This is meant to be somewhere in your path.  I've tested in Windows where I have 
Python files set to execute.  Change the path at the top unless your name is David and you are in Windows and are partial to miniconda.  

# Typical use case:

### Make sure you're not missing photos

c:\pictures> hashit store pictures
e:\pictures> hashit check pictures --diff --recursive --listonly > files_not_on_c.txt

### See if your new-found backup has anything new in it

c:\audio\my_awesome_band> hashit store bandmusic
f:\awesome_band_backup_from_1999> hashit check bandmusic --recursive

### Confirm your backup

g:\backup> hashit store backup --recursive
c:\necessary_files> hashit check backup --recursive --diff

# Options

**Usage:**
: `python hashit <action> <collection>`

###Actions:

**store**
: add files in current directory (and optionally subdirectories) to a collection

**check**
: see if files in current directory exist in a collection

**list**
: list the contents of a collection

**flush**
: clear out the contents of a collection and remove its file

---

###Optional:

--diff
: only show files that do not exist in the collection

--recursive
: recurse through subdirectories

--listonly
: only outputs the filenames, useful in piping the output to a file.

--rename
: renames the files in the current directory to "duplicate__<filename>".  This helps when reviewing old backup drives to quickly find non-duplicates in a directory by sorting in your OS's explorer/finder. 

--unrename
: removes the "duplicate__" from the front of files which exist in the collection.  Useful for both regret and temporarily weeding out non duplicates and then renaming them back.  