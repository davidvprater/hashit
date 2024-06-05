# hashit
Hashing script in Python to store and check file hashes, typically for duplicate checking.

It does a very simple SHA256 hash, which is less prone to collision than MD5.  I understand collisions are still possible, but they'd be very rare.

It creates an SQLite database file per collection in your home directory under .hashes/ 

**Note:** This is meant to be somewhere in your path.  I've tested in Windows where I have 
Python files set as executable.  

# Typical use case:

Let's assume that you have python files executable in your OS.  If you don't, add `python` before `hashit`.  You know what to do.

---

### Generate a text file of files missing from your main picture collection

c:\pictures> `hashit store pictures --recursive`

e:\pictures> `hashit check pictures --diff --recursive --listonly > files_not_on_c.txt`

*protip* Review the text file and if you want to copy them all, you can something like this:

(windows) `for /f "delims=" %i in (files_not_on_c.txt) do copy "%i" "c:\pictures\newfound"` 

(linux) `cat filenames_not_in_home.txt | xargs -I {} cp "{}" ~/Pictures/newfound/`

### See if your new-found backup has anything new in it

c:\audio\my_awesome_band> `hashit store bandmusic`

f:\awesome_band_backup_from_1999> `hashit check bandmusic --recursive`

### Confirm your backup

g:\backup> `hashit store backup --recursive`

c:\necessary_files> `hashit check backup --recursive --diff`

# Options

**Usage:**
: `python hashit <action> <collection>`

---

### Actions:

**store**
: add files in current directory (and optionally subdirectories) to a collection

**check**
: see if files in current directory exist in a collection

**list**
: list the contents of a collection

**flush**
: clear out the contents of a collection and remove its file

---
 
### Optional:

**--diff**
: only show files that do not exist in the collection

**--recursive**
: recurse through subdirectories

**--listonly**
: only outputs the filenames, useful in piping the output to a file.

**--rename**
: renames the files in the current directory to "duplicate__<filename>".  This helps when reviewing old backup drives to quickly find non-duplicates in a directory by sorting in your OS's explorer/finder. 

**--unrename**
: removes the "duplicate__" from the front of files which exist in the collection.  Useful for both regret and temporarily weeding out non duplicates and then renaming them back.  