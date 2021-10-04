import argparse


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("nr_cpus", help="Number of cpus", nargs=1)
    parser.add_argument("cpus", help="The cpus", nargs='*')

    args = parser.parse_args()

    nr_cpus = int(args.nr_cpus[0])

    cpu_bit_list = []
    for i in range(0, nr_cpus):
        cpu_bit_list.append('0')

    for cpu_string in args.cpus:
        cpu = int(cpu_string)
        cpu_bit_list[cpu] = '1'

    print(to_cpu_set(cpu_bit_list))
    print("irq_cpu_mask: " + to_irq_cpu_mask(cpu_bit_list))


def to_cpu_set(cpu_bit_list):
    cpu_set = "CPUSET=\"--cpuset "
    first = True
    for cpu in range(0, len(cpu_bit_list)):
        if cpu_bit_list[cpu] == '0':
            if first:
                first = False
            else:
                cpu_set = cpu_set + ","
            cpu_set = cpu_set + str(cpu)
    cpu_set = cpu_set + '"'
    return cpu_set


def to_irq_cpu_mask(cpu_bit_list):
    cpu_bit_list.reverse()

    s = "".join(cpu_bit_list)

    a = hex(int(s, 2))

    # remove the first 2 chars (0x)
    a = a[2:]

    # prefix with zero's
    a = a.zfill(24)

    r = ""
    for i in range(0, 24):
        if i % 8 == 0:
            if i > 0:
                r += ","
            r += "0x"
        r += a[i]
    return r
