#! /usr/bin/perl

# Принять как параметр папку в текущем каталоге.
# Папка должна быть типа 12345.6789.
# Удалить здесь все папки того же типа,
# которые меньше имени папки

use warnings;
use strict;

my $dir = shift or die "No folder to leave here specified\n";
my $dir_qr = qr/^\d+\.\d+$/;
$dir =~ /$dir_qr/ or die "Invalid folder name";

opendir DIR, ".";
while (readdir DIR) {
    next unless -d $_;
    next unless /$dir_qr/;
    next if $_ >= $dir || $_ eq $dir;
    `rm -r $_`;
}
closedir DIR;
