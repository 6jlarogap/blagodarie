#! /bin/bash

# --- configurable parameters ------------------------
VER_="prod"
GIT_BRANCH_="master"
# --- end of configurable parameters -----------------

root_dir_="/home/www-data/blagodari.rf.busted"
root_site_="blagodarie"

cd "$root_dir_/git/$VER_"
git checkout "$GIT_BRANCH_"
git pull

rm -rf "$root_dir_/busted/$VER_/$root_site_"
cp -pr "$root_site_" "$root_dir_/busted/$VER_/"

cd "$root_dir_/busted/"
grunt "cacheBust:$VER_"

new_root_site_=`date "+%s.%0N"`
cd "$root_dir_/busted/$VER_/"
mv "$root_site_" "$new_root_site_"

cd "$root_dir_/link/"
ln -sfn "$root_dir_/busted/$VER_/$new_root_site_" "$VER_"

cd "$root_dir_/busted/$VER_/"
../leave_only.pl "$new_root_site_"
