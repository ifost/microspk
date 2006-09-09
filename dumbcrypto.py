import random

carmichael_protection = 100

def is_prime(x):
    r = carmichael_protection
    if carmichael_protection > x:
        r = x-1
    for i in range(2,r):
        q = pow(i,x-1,x)
        if q != 1L:
            return 0
    return 1


#def is_prime_RabinMiller(x):
#    compute_b_copy = x - 1
#    b=0
#    while compute_b_copy % 2 == 0:
#        compute_b_copy = compute_b_copy + 1
#        b = b + 1
#    m = (x - 1)/          

def makelongnumber(numdigits):
    attempt = random.randint(1,9)
    for i in range(numdigits-2):
        attempt = attempt * 10L + random.randint(0,9)
    attempt = attempt * 10L + ([1,3,5,7,9][random.randint(0,4)])
    return attempt
        
def makeprime(numdigits):
    while 1:
        attempt = makelongnumber(numdigits)
        if is_prime(attempt):
            return attempt

def modular_keys(numdigits):
    p = makeprime(numdigits)
    q = makeprime(numdigits)
    modulus = p * q
    group_order = modulus - p - q + 1
    private_key = makelongnumber(2*numdigits)
    while private_key > modulus:
        private_key = makelongnumber(2*numdigits)
    public_key = lcm(private_key,group_order+1) / private_key
    return (public_key,private_key,modulus)
    #public_key = group_order
    # need to make it so that   private * public = 1 mod group_order
    # hmm,  smallest public  so that   lcm(private,group_order+1)/private


def gcd(x,y):
    z = x % y
    if z == 0:
        return y
    else:
        return gcd(y,z)

def lcm(x,y):
    return x * y / gcd(x,y)


def extendedEuclidean(u,v):
    def is_odd(x): return (x % 2L) == 1
    def is_even(x): return (x % 2L)
    if (u < v): (u,v) = (v,u)
    k = 0L
    while (is_even(u) and is_even(v)):
        u = u / 2L
        v = v / 2L
        k = k + 1
    (u1,u2,u3,t1,t2,t3) = (1L,0,u,v,u-1L,v)
    while 1:
        while 1:
            if (is_even(u3)):
                if (is_odd(u1) || is_odd(u2)):
                    u1 = u1 + v
                    u2 = u2 + u
                u1 = u1 / 2
                u2 = u2 / 2
                u3 = u3 / 2
            if (is_even(t3) or (u3 < t3)):
                (u1,u2,u3,t1,t2,t3) = (t1,t2,t3,u1,u2,u3)
            if (is_odd(u3)): break
        while ((u1 < t1) or (u2 < t2)):
            u1 = u1 + v
            u2 = u2 + u
        (u1,u2,u3) = (u1 - t1, u2 - t2, u3 - t3)
        if (t3 <= 0): break
    while ((u1 > v) and (u2 > u)):
        (u1,u2) = (v,u)
    (u1,u2,u3) = (u1 << k,u2 << k, u3 << k)
    return (u1,u2,u3)
