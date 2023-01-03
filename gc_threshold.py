import math
import dataclasses


@dataclasses.dataclass
class Gen:
    threshold: int
    target: float
    min_threshold: int
    max_threshold: int
    count: int = 0  # number of allocations or times collected
    size: int = 0  # number of objects
    trash: int = 0  # number of trash objects


GENS = [
    Gen(700, 0.2, 700, 5000),
    Gen(10, 0.4, 10, 200),
    Gen(10, 0.6, 10, 200),
]


def adapt_threshold(gen, generation_size, collected):
    threshold = gen.threshold
    target = gen.target
    # Calculate the current ratio of collected objects to generation size
    ratio = collected / generation_size

    # Use a formula to adjust the threshold based on the difference between
    # the current ratio and the target, and smoothly saturate towards the
    # maximum value of MIN/MAX_THRESHOLD using a sigmoid function that grows
    # saturates around 0 and 1;

    if ratio > target:
        # If the ratio is greater than the target, reduce the threshold
        min_threshold = gen.min_threshold
        exponent = -((ratio - target) * 10.0 - 5)
        exxp = 1.0 / (1.0 + math.exp(exponent))
        new_threshold = threshold + (min_threshold - threshold) * exxp

    elif ratio < target:
        # If the ratio is smaller than the target, increase the threshold
        max_threshold = gen.max_threshold
        exponent = -((target - ratio) * 10.0 - 5)
        exxp = 1.0 / (1.0 + math.exp(exponent))
        new_threshold = threshold + (max_threshold - threshold) * exxp
    else:
        # If the ratio is equal to the target, do not change the threshold
        new_threshold = threshold
    return math.ceil(new_threshold)


def main():

    # ratio of newly allocated objects that are trash
    trash_ratio = 0.02

    # ratio of collected objects that are actually trash but kept alive
    # due to references from objects in older generations
    long_lived_ratio = 0.01

    N = 100_000  # number of minor collections

    def run_collect():
        generation = 0
        for gen in reversed(GENS):
            # FIXME: add long_lived logic
            if gen.count > gen.threshold:
                generation = GENS.index(gen)
                break
        print(f'collect {generation}')
        for i, g in enumerate(GENS):
            print(
                f'  {i} count={g.count} size={g.size:,} trash={g.trash} threshold={g.threshold}'
            )
        try:
            older_gen = GENS[generation + 1]
        except IndexError:
            older_gen = GENS[-1]
        size = 0
        trash = 0
        for g in GENS:
            size += g.size
            trash += g.trash
            g.size = 0
            g.trash = 0
            g.count = 0
            if g is gen:
                break
        older_gen.size += size
        older_gen.count += 1
        if older_gen is gen:
            older_gen.trash = 0  # collected oldest gen
        else:
            older_gen.trash = int(size * long_lived_ratio)
        gen.threshold = adapt_threshold(gen, size, trash)

    for i in range(N):
        new = GENS[0].threshold
        trash = math.ceil(new * trash_ratio)
        GENS[0].size += new
        GENS[0].count += new
        GENS[0].trash += trash
        run_collect()


if __name__ == '__main__':
    main()
