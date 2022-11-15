export OUTPUT_DIR="log"
export OUTPUT_FILE="flower_output"
export MAIN=""
# concat string
for VARIABLE in $(seq 1 1 50)
do export MAIN="$MAIN nohup python main.py >$OUTPUT_DIR/${OUTPUT_FILE}${VARIABLE} 2>&1 &"
done
eval "$MAIN"

# seq (start, step, end)
for VARIABLE in $(seq 51 1 1000)
do export MAIN="nohup python main.py >$OUTPUT_DIR/${OUTPUT_FILE}${VARIABLE} 2>&1 &"
echo "$MAIN"
eval "$MAIN"
sleep 300s
done

#python main.py > log/flower_output 2>&1