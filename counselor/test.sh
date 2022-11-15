export OUTPUT_DIR="log"
export OUTPUT_FILE="flower_output"
export MAIN=""


for VARIABLE in $(seq 1 51 100)
do export MAIN="$MAIN nohup python main.py >$OUTPUT_DIR/${OUTPUT_FILE}${VARIABLE} 2>&1 &"
echo "$MAIN"
sleep 300s
done

#python main.py > log/flower_output 2>&1