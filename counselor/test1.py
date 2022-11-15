
d = [-1] * 50

def f(n):
    if (n == 0 or n == 1): return n
    if d[n] != -1:
        # use memory
        return d[n]
    # calculate
    print("n:", n)
    d[n] = f(n-1) + f(n-2)
    return d[n]

print(f(40))