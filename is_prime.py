

def is_prime(n: int) -> bool:
    if not isinstance(n, int):
        return False
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    if n % 3 == 0:
        return n == 3
    limit = math.isqrt(n)
    i = 5
    while i <= limit:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

if __name__ == "__main__":
    # Basic assertions
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 97, 101, 127, 9973]
    for p in primes:
        assert is_prime(p), f"Expected prime: {p}"

    nonprimes = [0, 1, 4, 6, 8, 9, 10, 12, 15, 21, 25, 27, 100, 1024, 9999]
    for c in nonprimes:
        assert not is_prime(c), f"Expected composite: {c}"

    print("Primes up to 50:", [n for n in range(2, 51) if is_prime(n)])

    # Optional: test numbers from command line
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            try:
                num = int(arg)
            except ValueError:
                print(f"{arg}: not an integer")
                continue
            print(f"{num}: {'prime' if is_prime(num) else 'not prime'}")
