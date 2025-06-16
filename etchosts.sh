#!/bin/bash
echo -e "$1 == $(getent ahostsv4 $1 | awk '{print $1}' RS=eof >&1)  ## \`getent ahostsv4 \$1 | awk '{print \$1}' RS=eof >&1\`" >&2
getent ahostsv4 $1 | awk '{print $1}' RS=eof >&1
