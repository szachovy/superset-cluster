file1="run.sh"
file2="./src/common.sh"
file3="./tests/testsuite/roles/testing/files/system.sh"

echo $((
  100
  -
  $(grep --extended-regexp '^[^#]*[[:alnum:]]' $file3 | wc --lines) * 100
  /
  (
    $(grep --extended-regexp '^[^#]*[[:alnum:]]' $file1 $file2 | wc --lines)
    +
    $(comm -12 <(grep --extended-regexp '^[^#]*[[:alnum:]]' $file1 | sort) <(grep --extended-regexp '^[^#]*[[:alnum:]]' $file3 | sort) | wc --lines)
  )
))
