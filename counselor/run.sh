export OUTPUT_DIR="log"
export OUTPUT_FILE="girl_output"
export MAIN=""
# concat string
for VARIABLE in $(seq 1 1 5)
do export MAIN="$MAIN nohup python main.py >$OUTPUT_DIR/${OUTPUT_FILE}${VARIABLE} 2>&1 &"
done
eval "$MAIN"