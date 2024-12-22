uv run pylint \
   --verbose \
   --output-format=text ./**/*.py \
| tee pylint-log.txt

score="$(
   sed -n "/^Your code has been rated at/{s,.* at \([0-9\.]*\)\/.*,\1,p}" \
      pylint-log.txt)"

uv run anybadge \
   --file="images/pylint.svg" \
   --label "pylint" \
   --overwrite \
   --value "$score"

rm -f pylint-log.txt
